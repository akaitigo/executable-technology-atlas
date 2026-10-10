# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import unittest,json,os,platform,datetime
DISCOUNT=0
TRACE=[];OUTCOMES=[]
isolation,order=sys.argv[1:3]
def quote():return 10-DISCOUNT
class QuoteTests(unittest.TestCase):
 def setUp(self):
  global DISCOUNT
  self.row={'test':self._testMethodName[5:],'setup_before':DISCOUNT}
  if isolation=='fixture':DISCOUNT=0
  self.row['setup_after']=DISCOUNT;TRACE.append(self.row)
 def tearDown(self):
  global DISCOUNT
  self.row['teardown_before']=DISCOUNT
  if isolation=='fixture':DISCOUNT=0
  self.row['teardown_after']=DISCOUNT
 def test_override(self):
  global DISCOUNT
  self.row['body_before']=DISCOUNT;DISCOUNT=2;self.row['body_after']=DISCOUNT;actual=quote();self.row.update(expected=8,actual=actual);self.assertEqual(actual,8)
 def test_default(self):
  self.row['body_before']=DISCOUNT;self.row['body_after']=DISCOUNT;actual=quote();self.row.update(expected=10,actual=actual);self.assertEqual(actual,10)
class Result(unittest.TextTestResult):
 def addSuccess(self,test):super().addSuccess(test);OUTCOMES.append({'test':test._testMethodName[5:],'outcome':'PASS'})
 def addFailure(self,test,err):super().addFailure(test,err);OUTCOMES.append({'test':test._testMethodName[5:],'outcome':'FAIL'})
 def addError(self,test,err):super().addError(test,err);OUTCOMES.append({'test':test._testMethodName[5:],'outcome':'ERROR'})
start=datetime.datetime.now(datetime.timezone.utc).isoformat();names=['override','default'] if order=='override-first' else ['default','override'];suite=unittest.TestSuite([QuoteTests('test_'+n) for n in names]);r=unittest.TextTestRunner(stream=sys.stderr,verbosity=2,resultclass=Result).run(suite)
for row,out in zip(TRACE,OUTCOMES):row['outcome']=out['outcome']
print(json.dumps(dict(pid=os.getpid(),python=platform.python_version(),isolation=isolation,order=order,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),success=r.wasSuccessful(),trace=TRACE,final_state=DISCOUNT),ensure_ascii=False));sys.exit(0 if r.wasSuccessful() else 1)
