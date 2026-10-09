import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import photos


def page():
    return {'title':'File:VW Golf GTE blue.jpg','categories':[{'title':'Category:Blue Volkswagen hatchbacks'},{'title':'Category:Volkswagen Golf VII GTE'}], 'imageinfo':[{'mime':'image/jpeg','thumburl':'https://thumb.wikimedia.org/test.jpg','descriptionurl':'https://commons.wikimedia.org/wiki/File:Test.jpg','extmetadata':{'Artist':{'value':'<a href="/test">Nicolas &amp; Co</a>'},'LicenseShortName':{'value':'CC BY-SA 4.0'},'LicenseUrl':{'value':'https://creativecommons.org/licenses/by-sa/4.0/'},'ImageDescription':{'value':'VW Golf GTE at a show'}}}]}

SELECTED=[{'model':{'merk':'VOLKSWAGEN','model':'Golf GTE','generatie':'VII'}}]

class PhotoTests(unittest.TestCase):
    def test_match_preserves_attribution_and_original_metadata(self):
        item=page();row=photos.match(item,'VOLKSWAGEN','GOLF GTE','BLAUW','VII')
        self.assertEqual(row['artist'],'Nicolas & Co')
        self.assertEqual(row['original_metadata'],item['imageinfo'][0]['extmetadata'])
        self.assertTrue(row['image_url'].startswith('/api/photo/'))

    def test_wrong_color_model_and_generation_rejected(self):
        for model,color,generation in [('GOLF GTI','BLAUW','VII'),('GOLF GTE','ROOD','VII'),('GOLF GTE','BLAUW','VIII')]:
            with self.subTest(model=model,color=color,generation=generation):
                self.assertIsNone(photos.match(page(),'VOLKSWAGEN',model,color,generation))

    def test_unlicensed_unsafe_interior_and_missing_author_rejected(self):
        for change in ('licence','url','interior','artist','restrictions'):
            item=page();info=item['imageinfo'][0];meta=info['extmetadata']
            if change=='licence':meta['LicenseShortName']['value']='All rights reserved'
            if change=='url':info['thumburl']='https://example.com/image.jpg'
            if change=='interior':item['title']+=' interior'
            if change=='artist':meta['Artist']['value']=''
            if change=='restrictions':meta['Restrictions']={'value':'noncommercial'}
            with self.subTest(change=change):self.assertIsNone(photos.match(item,'VOLKSWAGEN','GOLF GTE','BLAUW','VII'))

    def test_generation_is_required_and_unknown_does_not_request(self):
        self.assertIsNone(photos.match(page(),'VOLKSWAGEN','GOLF GTE','BLAUW'))
        vehicle={'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE','eerste_kleur':'BLAUW'}
        for selection in ([],[{'model':{'merk':'VOLKSWAGEN','model':'Golf GTE','generatie':'onbekend'}}],[{'model':{'merk':'VOLKSWAGEN','model':'Polo','generatie':'VI'}}]):
            with tempfile.TemporaryDirectory() as root,patch('photos.read_json') as read:
                rows,reason=photos.find(vehicle,selection,root)
                self.assertEqual(rows,[]);self.assertIn('niet beschikbaar',reason);read.assert_not_called()

    def test_generation_must_be_attached_to_same_model(self):
        item=page();item['categories']=[{'title':'Category:Blue Volkswagen hatchbacks'},{'title':'Category:Volkswagen Polo VII'}]
        self.assertIsNone(photos.match(item,'VOLKSWAGEN','GOLF GTE','BLAUW','VII'))

    def test_conflicting_generation_is_rejected(self):
        item=page();item['title']='File:VW Golf VIII GTE blue.jpg'
        self.assertIsNone(photos.match(item,'VOLKSWAGEN','GOLF GTE','BLAUW','VII'))

    def test_facelift_must_be_explicit_and_agree(self):
        self.assertIsNone(photos.match(page(),'VOLKSWAGEN','GOLF GTE','BLAUW','VII facelift'))
        item=page();item['imageinfo'][0]['extmetadata']['ImageDescription']['value']='VW Golf VII GTE facelift'
        self.assertIsNotNone(photos.match(item,'VOLKSWAGEN','GOLF GTE','BLAUW','VII facelift'))
        self.assertIsNone(photos.match(item,'VOLKSWAGEN','GOLF GTE','BLAUW','VII'))

    def test_obsolete_query_cache_is_not_reused(self):
        import hashlib
        with tempfile.TemporaryDirectory() as root,patch('photos.read_json',return_value={}) as read:
            folder=Path(root)/'photos';folder.mkdir()
            key=hashlib.sha256(json.dumps(('VOLKSWAGEN','GOLF GTE','BLAUW','VII')).encode()).hexdigest()
            (folder/('query-'+key+'.json')).write_text(json.dumps({'fetched_at':99999999999,'rows':[{'wrong':'old photo'}],'reason':'old'}))
            rows,_=photos.find({'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE','eerste_kleur':'BLAUW'},SELECTED,root)
            self.assertEqual(rows,[]);read.assert_called_once()

    def test_missing_identity_does_not_request_provider(self):
        with tempfile.TemporaryDirectory() as root,patch('photos.read_json') as read:
            rows,reason=photos.find({'merk':'TEST'},[],root)
            self.assertEqual(rows,[]);self.assertTrue(reason);read.assert_not_called()

    def test_cache_and_no_plate_or_vin_in_query(self):
        with tempfile.TemporaryDirectory() as root,patch('photos.read_json',return_value={'query':{'pages':{'1':page()}}}) as read:
            vehicle={'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE','eerste_kleur':'BLAUW','kenteken':'SECRETPLATE','vin':'SECRETVIN'}
            first=photos.find(vehicle,SELECTED,root);second=photos.find(vehicle,SELECTED,root)
            self.assertEqual(first,second);self.assertEqual(len(first[0]),1);read.assert_called_once()
            self.assertNotIn('SECRET',read.call_args.args[0])
            ident=first[0][0]['id']
            with patch('photos.request',return_value=(b'image','image/jpeg')) as download:
                self.assertEqual(photos.media(ident,root),(b'image','image/jpeg'))
                self.assertEqual(photos.media(ident,root),(b'image','image/jpeg'));download.assert_called_once()

    def test_empty_results_negative_cache(self):
        with tempfile.TemporaryDirectory() as root,patch('photos.read_json',return_value={}) as read:
            v={'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE','eerste_kleur':'BLAUW'}
            rows,reason=photos.find(v,SELECTED,root);photos.find(v,SELECTED,root)
            self.assertEqual(rows,[]);self.assertIn('Geen herbruikbare foto',reason);read.assert_called_once()

    def test_provider_error_is_distinct(self):
        with tempfile.TemporaryDirectory() as root,patch('photos.read_json',return_value={'error':{}}):
            with self.assertRaises(photos.PhotoError):photos.find({'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE','eerste_kleur':'BLAUW'},SELECTED,root)

    def test_unknown_photo_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for ident in ('../secret','a'*64):
                with self.assertRaises(FileNotFoundError):photos.media(ident,root)
        self.assertFalse(photos.safe_url('https://thumb.wikimedia.org:bad/image',{'thumb.wikimedia.org'}))

    def test_unsupported_download_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)/'photos';folder.mkdir();(folder/('a'*64+'.json')).write_text(json.dumps({'thumbnail_source_url':'https://thumb.wikimedia.org/test.jpg'}))
            with patch('photos.request',return_value=(b'html','text/html')):
                with self.assertRaises(photos.PhotoError):photos.media('a'*64,root)
