import unittest
import importlib

import taxonomic_grammar as tg
from nerve_center import nerve

class TestNerveFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        importlib.reload(tg)
        # simple prompt
        cls.prompt = 'electron configuration valence chemistry'
        cls.result = tg.analyze(cls.prompt)
        cls.sid = nerve.create_session(cls.result, meta={'test': True})

    def test_session_created(self):
        self.assertIsNotNone(self.sid)
        s = nerve.sessions.get(self.sid)
        self.assertIsNotNone(s)
        self.assertIn('items', s)
        self.assertTrue(isinstance(s['items'], list))

    def test_conjecture_structure(self):
        opts = nerve.conjecture_sinewave(self.sid, steps=3)
        self.assertIsInstance(opts, list)
        self.assertGreaterEqual(len(opts), 1)
        for o in opts:
            # allow either dict or string fallback
            if isinstance(o, dict):
                self.assertIn('variable', o)
                self.assertIn('text', o)
            else:
                self.assertIsInstance(o, str)

    def test_expand_and_chain(self):
        opts = nerve.conjecture_sinewave(self.sid, steps=3)
        # find first dict option with variable
        var = None
        for o in opts:
            if isinstance(o, dict) and o.get('variable'):
                var = o.get('variable')
                break
        if not var:
            self.skipTest('no variable available to expand')
        out = nerve.expand_variable(self.sid, var)
        self.assertIsInstance(out, str)
        # chain
        chained = nerve.chain_from_variable(self.sid, var, steps=2)
        self.assertIsInstance(chained, list)
        self.assertGreaterEqual(len(chained), 1)
        for c in chained:
            self.assertTrue(isinstance(c, dict) or isinstance(c, str))

    def test_generate_variations_conditional(self):
        outs = tg.generate_variations_conditional(self.result, steps=4, minimal=True, reverse=True)
        self.assertIsInstance(outs, list)
        self.assertEqual(len(outs), 4)
        for o in outs:
            self.assertIsInstance(o, str)

if __name__ == '__main__':
    unittest.main()
