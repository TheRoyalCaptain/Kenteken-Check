import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import accounts
import app
import reports
import worker

PASSWORD='a strong test password 2026'
class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.patcher=patch.object(app,'DATA',self.root);self.patcher.start()
    def tearDown(self):self.patcher.stop();self.temp.cleanup()
    def request(self,path,method='GET',data=None,token='',csrf=True,origin='http://localhost',query='',count=False):
        raw=json.dumps(data or {}).encode();statuses=[]
        env={'PATH_INFO':path,'REQUEST_METHOD':method,'QUERY_STRING':query,'CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw),'HTTP_HOST':'localhost','HTTP_ORIGIN':origin,'REMOTE_ADDR':'127.0.0.1','HTTP_X_KC_REQUEST':'1','HTTP_COOKIE':'kc_session='+token}
        if csrf and token:env['HTTP_X_CSRF_TOKEN']=accounts.csrf(token)
        if count:env['HTTP_X_LOOKUP_COUNT']='1'
        body=b''.join(app.application(env,lambda s,h:statuses.append((s,dict(h)))))
        return statuses[0][0],statuses[0][1],json.loads(body)
    def user(self,name='alice',role='user'):
        user=accounts.create(self.root,name,PASSWORD,role);return user,accounts.issue(self.root,user)
    def test_persistent_personal_lookup_counter(self):
        alice,token=self.user();bob,other=self.user('bob')
        with patch.object(app,'lookup',side_effect=lambda *a,**k:{'plate':'AB123C'}):
            self.assertTrue(self.request('/api/vehicle/AB123C',token=token,count=True,csrf=False)[0].startswith('403'))
            for expected in (1,2,3):
                self.assertEqual(self.request('/api/vehicle/AB123C',token=token,count=True)[2]['lookup_count'],expected)
            for query in ('','refresh=1','selection=%7B%7D'):
                self.assertEqual(self.request('/api/vehicle/AB123C',token=token,query=query,count=bool(query))[2]['lookup_count'],3)
            self.assertEqual(self.request('/api/vehicle/AB123C',token=other)[2]['lookup_count'],0)
            self.assertEqual(self.request('/api/vehicle/AB123C',token=other,count=True)[2]['lookup_count'],1)
        with patch.object(app,'lookup',side_effect=app.LookupError('Ongeldig',400)):
            self.assertTrue(self.request('/api/vehicle/invalid',token=token,count=True)[0].startswith('400'))
        self.assertEqual(accounts.lookup_count(self.root,alice['id'],'AB123C'),3)
        context=app.CURRENT_USER.set(alice['id'])
        try:
            data={'plate':'AB123C'};app.add_lookup_count(data,{'REQUEST_METHOD':'HEAD','HTTP_X_LOOKUP_COUNT':'1'},{});self.assertEqual(data['lookup_count'],3)
        finally:app.CURRENT_USER.reset(context)
    def test_lookup_counter_atomic_updates(self):
        from concurrent.futures import ThreadPoolExecutor
        user,_=self.user()
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _:accounts.lookup_count(self.root,user['id'],'AB123C',True),range(40)))
        self.assertEqual(accounts.lookup_count(self.root,user['id'],'AB123C'),40)
    def test_hash_salt_verification_no_plaintext_and_cookie_attributes(self):
        a=accounts.password_hash(PASSWORD);b=accounts.password_hash(PASSWORD)
        self.assertNotEqual(a,b);self.assertTrue(accounts.verify(PASSWORD,a));self.assertFalse(accounts.verify('wrong',a));self.assertNotIn(PASSWORD,a)
        self.assertIn('HttpOnly',accounts.cookie('token',{}));self.assertIn('SameSite=Lax',accounts.cookie('token',{}));self.assertIn('Secure',accounts.cookie('token',{'wsgi.url_scheme':'https'}))
    def test_all_data_routes_require_auth_and_setup_is_single_use(self):
        for path in ['/api/vehicle/AB123C','/api/vin/WVWZZZCDZMW123456','/api/history/AB123C','/api/reports/AB123C','/api/report-file/AB123C/'+'a'*32,'/api/photo/'+'a'*64,'/api/garage','/api/preferences']:
            self.assertTrue(self.request(path)[0].startswith('401'),path)
        self.assertTrue(self.request('/auth/setup','POST',{'username':'admin','password':PASSWORD})[0].startswith('200'))
        self.assertTrue(self.request('/auth/setup','POST',{'username':'second','password':PASSWORD})[0].startswith('409'))
        self.assertTrue(self.request('/auth/state')[2]['setup'] is False)
    def test_csrf_origin_role_checks_and_hashed_sessions(self):
        user,token=self.user()
        self.assertTrue(self.request('/api/garage/AB123C','PUT',{'watch':True},token,False)[0].startswith('403'))
        self.assertTrue(self.request('/api/garage/AB123C','PUT',{'watch':True},token,origin='http://evil.invalid')[0].startswith('403'))
        self.assertTrue(self.request('/auth/users',token=token)[0].startswith('403'))
        self.assertTrue(self.request('/api/vehicle/AB123C',token=token,csrf=False,query='refresh=1')[0].startswith('403'))
        self.assertTrue(self.request('/api/vin/WVWZZZCDZMW123456',token=token,csrf=False,query='selection=%7B%22vin_decode_enabled%22%3Atrue%7D')[0].startswith('403'))
        with accounts.database(self.root) as db:
            self.assertEqual(db.execute('SELECT hash FROM sessions').fetchone()[0],accounts.token_hash(token))
            self.assertNotIn(token,(self.root/'platform.sqlite').read_bytes().decode(errors='ignore'))
    def test_user_data_reports_preferences_and_favorites_are_isolated(self):
        alice,a=self.user();bob,b=self.user('bob')
        self.request('/api/garage/AB123C','PUT',{'watch':True},a)
        self.request('/api/preferences','POST',{'key':'recent','value':['AB123C']},a)
        self.assertEqual(self.request('/api/garage',token=b)[2]['favorites'],[])
        self.assertEqual(self.request('/api/preferences',token=b)[2],{})
        context=app.CURRENT_USER.set(alice['id'])
        try:
            app.remember({'plate':'AB123C','fetched_at':time.time(),'sections':{'voertuig':[{'merk':'SECRET'}]},'sources':{'voertuig':{'label':'Voertuig'}}})
            doc=reports.save_document(app.storage_dir(),'AB123C','secret.pdf',b'%PDF-1.7 private')
        finally:app.CURRENT_USER.reset(context)
        self.assertEqual(self.request('/api/history/AB123C',token=b)[2]['observations'],[])
        self.assertEqual(self.request('/api/reports/AB123C',token=b)[2],[])
        self.assertTrue(self.request('/api/report-file/AB123C/'+doc['id'],token=b)[0].startswith('404'))
        self.assertEqual(len(self.request('/api/history/AB123C',token=a)[2]['observations']),1)
    def test_password_change_logout_expiry_and_disable_revoke_sessions(self):
        user,token=self.user('admin','admin');other,second=self.user('other')
        extra=accounts.issue(self.root,user)
        status,headers,result=self.request('/auth/password','POST',{'current_password':PASSWORD,'password':'another strong password'},token)
        self.assertTrue(status.startswith('200'));self.assertIn('HttpOnly',headers['Set-Cookie'])
        self.assertTrue(self.request('/api/garage',token=extra)[0].startswith('401'))
        fresh=headers['Set-Cookie'].split(';')[0].split('=')[1]
        self.request('/auth/users/'+str(other['id']),'POST',{'active':False},fresh)
        self.assertTrue(self.request('/api/garage',token=second)[0].startswith('401'))
        self.request('/auth/logout','POST',{},fresh)
        self.assertTrue(self.request('/api/garage',token=fresh)[0].startswith('401'))
        expired=accounts.issue(self.root,user)
        with accounts.database(self.root) as db:db.execute('UPDATE sessions SET seen=? WHERE hash=?',(time.time()-1801,accounts.token_hash(expired)))
        self.assertTrue(self.request('/api/garage',token=expired)[0].startswith('401'))
    def test_login_throttle_and_weak_password_rejected(self):
        with self.assertRaises(accounts.AccountError):accounts.create(self.root,'alice','admin')
        for _ in range(10):accounts.throttle(self.root,'user:test',10)
        with self.assertRaises(accounts.AccountError) as raised:accounts.throttle(self.root,'user:test',10)
        self.assertEqual(raised.exception.status,429)
        self.assertTrue(self.request('/auth/login','POST',{'username':'missing','password':PASSWORD})[0].startswith('401'))
    def test_four_retained_versions_unchanged_deduplicates_outage_preserves(self):
        user,_=self.user();context=app.CURRENT_USER.set(user['id'])
        try:
            for value in range(6):app.remember({'plate':'AB123C','fetched_at':100+value,'sources':{},'sections':{'voertuig':[{'version':value}]}})
            app.remember({'plate':'AB123C','fetched_at':200,'sources':{},'sections':{'voertuig':[{'version':5}]}})
            app.remember({'plate':'AB123C','fetched_at':201,'sources':{},'warnings':['outage'],'sections':{'voertuig':None}})
            data=app.history('AB123C',True)['observations']
            self.assertEqual(len(data),4);self.assertEqual([x['data']['sections']['voertuig'][0]['version'] for x in data],[2,3,4,5]);self.assertEqual(data[-1]['last_seen_at'],200)
        finally:app.CURRENT_USER.reset(context)
    def test_daily_worker_leases_restarts_pause_and_failure_retry(self):
        user,_=self.user();accounts.favorite(self.root,user['id'],'AB123C',True)
        with accounts.database(self.root) as db:db.execute('UPDATE favorites SET next_due=100')
        job=accounts.claim(self.root,101);self.assertIsNotNone(job);self.assertIsNone(accounts.claim(self.root,102));self.assertIsNotNone(accounts.claim(self.root,1902))
        with accounts.database(self.root) as db:db.execute('UPDATE favorites SET lease=0')
        with patch.object(app,'lookup',return_value={'warnings':[]}) as lookup:
            self.assertTrue(worker.run_once(2000));lookup.assert_called_once_with('AB123C',refresh=True);self.assertFalse(worker.run_once(2001))
        with patch.object(app,'lookup',side_effect=RuntimeError('secret provider key')):self.assertTrue(worker.run_once(2000+86400))
        row=accounts.favorites(self.root,user['id'])[0];self.assertNotIn('secret',row['error']);self.assertEqual(row['next_due'],2000+86400+3600)
        accounts.favorite(self.root,user['id'],'AB123C',False);self.assertFalse(worker.run_once(999999))
    def test_first_admin_migrates_legacy_history_and_reports(self):
        for value in range(6):app.remember({'plate':'AB123C','fetched_at':100+value,'sources':{},'sections':{'voertuig':[{'merk':'LEGACY','version':value}]}})
        reports.save_document(self.root,'AB123C','legacy.pdf',b'%PDF-1.7 legacy')
        status,headers,result=self.request('/auth/setup','POST',{'username':'admin','password':PASSWORD})
        self.assertTrue(status.startswith('200'));self.assertFalse((self.root/'cache.sqlite').exists())
        context=app.CURRENT_USER.set(result['user']['id'])
        try:self.assertEqual(len(app.history('AB123C')['observations']),4);self.assertEqual(app.history('AB123C',True)['observations'][0]['data']['sections']['voertuig'][0]['merk'],'LEGACY');self.assertEqual(len(reports.documents(app.storage_dir(),'AB123C')),1)
        finally:app.CURRENT_USER.reset(context)
