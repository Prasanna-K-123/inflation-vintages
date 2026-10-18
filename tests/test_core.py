import unittest
from datetime import datetime,timedelta
from inflation_vintages.core import VintageStore,shift_month,baseline_predictions,ar1_prediction

def row(month,value,when,base=2012):
    return {'reference_month':month,'value':value,'published_at':when,'base':base,'metric':'headline_yoy_percent','sector':'Combined','status':'test'}

class VintageTests(unittest.TestCase):
    def setUp(self):
        self.p='2024-02-12T17:30:00+05:30';self.f='2024-03-12T17:30:00+05:30'
        self.a=row('2024-01',5.1,self.p);self.b=row('2024-01',5.2,self.f)

    def test_revision_timing_and_equality(self):
        s=VintageStore([self.a,self.b])
        self.assertEqual(s.asof('2024-01',self.p)['value'],5.1)
        just_before=datetime.fromisoformat(self.f)-timedelta(minutes=1)
        self.assertEqual(s.asof('2024-01',just_before)['value'],5.1)
        self.assertEqual(s.asof('2024-01',self.f)['value'],5.2)

    def test_future_changes_do_not_change_past_query(self):
        s=VintageStore([self.a,row('2024-01',999,self.f),row('2024-02',999,self.f)])
        self.assertEqual(s.asof('2024-01',self.p)['value'],5.1)

    def test_missing_base_and_vintage_are_errors(self):
        s=VintageStore([self.a])
        with self.assertRaises(ValueError):s.asof('2024-01','2024-01-01T00:00:00+05:30')
        with self.assertRaises(ValueError):s.asof('2024-01',self.p,base=2024)
        with self.assertRaises(ValueError):s.asof('2024-02',self.p)

    def test_conflicting_vintage_rejected_identical_collapsed(self):
        with self.assertRaises(ValueError):VintageStore([self.a,row('2024-01',6,self.p)])
        self.assertEqual(len(VintageStore([self.a,self.a]).rows),1)

    def test_timezone_required(self):
        with self.assertRaises(ValueError):VintageStore([row('2024-01',5,'2024-02-12T17:30:00')])
        with self.assertRaises(ValueError):VintageStore([self.a]).asof('2024-01','2024-02-12T17:30:00')

    def test_month_boundary_and_baseline_identities(self):
        self.assertEqual(shift_month('2024-01',-1),'2023-12');self.assertEqual(shift_month('2024-01',-12),'2023-01')
        s=VintageStore([self.a,row('2023-02',6,self.p)])
        self.assertEqual(baseline_predictions(s,'2024-02',self.p),{'persistence':5.1,'seasonal_12month':6})

    def test_ar1_manual_arithmetic(self):
        m={'intercept_standardized':5.,'coefficient_standardized':.8,'feature_mean':4.,'feature_scale':2.}
        self.assertAlmostEqual(ar1_prediction(6.,m),5.8)

if __name__=='__main__':unittest.main()
