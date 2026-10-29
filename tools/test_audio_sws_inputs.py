# SPDX-License-Identifier: Apache-2.0
import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from prepare_audio_sws import prepare
from verify_audio_sws_inputs import verify
ROOT=Path(__file__).resolve().parents[1]
class AudioSwsInputsTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.vendor=self.root/'vendor';self.vendor.mkdir()
        shutil.copyfile(ROOT/'audio-sws-inputs.json',self.vendor/'audio-sws-inputs.json')
        self.stock=self.root/'stock'
        for item in json.loads((ROOT/'audio-sws-inputs.json').read_text())['inputs']:
            destination=self.stock/item['source'].lstrip('/')
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/item['proprietary_path'],destination)
    def make(self):
        return prepare(self.vendor,self.stock/'product',self.stock/'odm')
    def corrupt(self,path):
        data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
    def test_canonical_payload(self):
        self.assertEqual(self.make(),14);self.assertEqual(verify(self.vendor),14)
        data=(self.vendor/'proprietary/system_ext/etc/honor/sws0730.bin').read_bytes()
        self.assertEqual(len(data),914208)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'290f047b22f7fe9790d1e254fe05e0954d48d10ce02c77f7285484a804239d17')
    def test_bad_stock_engine_refuses_before_destination_write(self):
        self.corrupt(self.stock/'product/lib64/lib64xisten7_3.so')
        with self.assertRaisesRegex(ValueError,'Stock SWS input mismatch'):self.make()
        self.assertFalse((self.vendor/'proprietary').exists())
    def test_bad_stock_tuning_refuses_before_destination_write(self):
        self.corrupt(self.stock/'odm/etc/sws/spaConfig.bin')
        with self.assertRaisesRegex(ValueError,'Stock SWS input mismatch'):self.make()
        self.assertFalse((self.vendor/'proprietary').exists())
    def test_generated_truncation_rejected(self):
        self.make();p=self.vendor/'proprietary/system_ext/etc/honor/sws0730.bin'
        p.write_bytes(p.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError,'SWS input mismatch'):verify(self.vendor)
    def test_changed_prebuilt_rejected(self):
        self.make();self.corrupt(self.vendor/'proprietary/product/lib64/lib64xisten7_3.so')
        with self.assertRaisesRegex(ValueError,'SWS input mismatch'):verify(self.vendor)
    def test_duplicate_inventory_rejected(self):
        self.make();p=self.vendor/'audio-sws-inputs.json';inventory=json.loads(p.read_text())
        inventory['inputs'][-1]=inventory['inputs'][0]
        p.write_text(json.dumps(inventory))
        with self.assertRaisesRegex(ValueError,'Invalid SWS inventory'):verify(self.vendor)
if __name__=='__main__':unittest.main()
