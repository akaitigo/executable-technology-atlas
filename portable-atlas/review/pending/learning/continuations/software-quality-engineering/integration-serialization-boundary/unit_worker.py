# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import unittest,json,os,platform
from domain import sender_domain,receive
fixture_id,number,mode=sys.argv[1:4];number=int(number)
class PureUnits(unittest.TestCase):
 def test_sender_domain(self):self.assertEqual(sender_domain(fixture_id,number),{'fixture_id':fixture_id,'delay_ms':number})
 def test_receiver_domain(self):self.assertEqual(receive({'fixture_id':fixture_id,'delay_ms':number},mode),number)
r=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(unittest.TestSuite([PureUnits('test_sender_domain'),PureUnits('test_receiver_domain')]))
print(json.dumps(dict(pid=os.getpid(),python=platform.python_version(),fixture_id=fixture_id,delay_ms=number,receiver=mode,tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),success=r.wasSuccessful(),covered_scope='pure canonical domain only; serializer/HTTP adapter not tested')));sys.exit(0 if r.wasSuccessful() else 1)
