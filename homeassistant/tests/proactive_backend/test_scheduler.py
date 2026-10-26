"""Pure scheduler contract, no Home Assistant import or network."""
import importlib.util
from pathlib import Path
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parents[2]/'custom_components/ha2_notifications/proactive.py'

class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(P.exists(), 'Missing proactive scheduler')
        s=importlib.util.spec_from_file_location('proactive_pure',P)
        self.p=importlib.util.module_from_spec(s);s.loader.exec_module(self.p)
    def test_exact_defaults_and_strict_validation(self):
        p=self.p
        self.assertEqual(p.DEFAULT_CONFIG,dict(enabled=False,all_day=True,start='09:00',end='21:00',interval_minutes=60,mode='cue'))
        self.assertEqual(p.validate_config(p.DEFAULT_CONFIG),p.DEFAULT_CONFIG)
        for change in ({'interval_minutes':True},{'interval_minutes':45},{'interval_minutes':0},{'start':'9:00'},{'end':'24:00'},{'all_day':1},{'mode':'<script>'},{'unexpected':1},{'enabled':'false'},{'all_day':False,'end':'09:00'}):
            with self.subTest(change=change),self.assertRaises(ValueError):p.validate_config(dict(p.DEFAULT_CONFIG,**change))
        with self.assertRaises(ValueError):p.validate_config({'enabled':False})
    def test_overnight_all_day_and_timezone(self):
        p=self.p;c=dict(p.DEFAULT_CONFIG,all_day=False,start='22:00',end='06:45');tz=ZoneInfo('Atlantic/Canary')
        for hour,minute,want in ((22,0,True),(6,44,True),(6,45,False),(12,0,False)):
            now=datetime(2026,12,1,hour,minute,tzinfo=tz)
            self.assertEqual(p.in_window(c,now,tz),want)
        self.assertTrue(p.in_window(dict(c,all_day=True),datetime.now(timezone.utc),tz))
        self.assertFalse(p.in_window(c,datetime(2026,1,1),tz))
    def test_uniform_seconds_unrounded_capped_and_intents(self):
        p=self.p
        class RNG:
            def uniform(self,lo,hi):self.bounds=(lo,hi);return lo+.123456
            def choice(self,items):self.items=items;return items[0]
        r=RNG();now=datetime(2026,1,1,tzinfo=timezone.utc)
        due=p.sample_due(dict(p.DEFAULT_CONFIG,interval_minutes=30),now,r)
        self.assertEqual(r.bounds,(1350,2250));self.assertEqual(due.microsecond,123456)
        p.sample_due(dict(p.DEFAULT_CONFIG,interval_minutes=1440),now,r)
        self.assertEqual(r.bounds,(64800,86400))
        chosen=p.choose_intent([p.INTENT_IDS[0]],r)
        self.assertNotEqual(chosen,p.INTENT_IDS[0]);self.assertNotIn(p.INTENT_IDS[0],r.items)
