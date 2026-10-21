"""Mutation checks for the message outcome oracle, independent of native flags."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from string_challenge import STRINGS,evaluate

def sample():
    rows=[];text='initial log\n'
    for phase,strings,suppressed in [('loaded-protection',STRINGS,True),('removed-protection',STRINGS,False),('reapplied-protection',[14665],True)]:
        for strref in strings:
            after=text if suppressed else text+'Actor: message '+str(strref)+'\n'
            rows.append(dict(phase=phase,strref=strref,expected_suppressed=suppressed,
                before_text=text,after_text=after,expected_text='message '+str(strref),apply_return_code=0,passed=True))
            text=after
    return dict(observations=rows,reapplied_parameter2_normalized=True)

class StringChallengeOracle(unittest.TestCase):
    def test_zero_return_codes_do_not_prevent_observed_success(self):
        self.assertTrue(all(r['passed'] for r in evaluate(sample())))

    def test_message_leak_fails_even_with_native_pass_flag(self):
        native=sample();native['observations'][0]['after_text']+='leaked'
        self.assertFalse(evaluate(native)[0]['passed'])

    def test_unrelated_appended_text_is_not_a_positive_control(self):
        native=sample();row=native['observations'][5];row['after_text']=row['before_text']+'unrelated'
        self.assertFalse(evaluate(native)[5]['passed'])

    def test_old_matching_text_is_not_new_display_evidence(self):
        native=sample();row=native['observations'][5]
        row['before_text']+=row['expected_text'];row['after_text']=row['before_text']+'unrelated'
        self.assertFalse(evaluate(native)[5]['passed'])

    def test_missing_case_cannot_pass(self):
        native=sample();native['observations'].pop()
        with self.assertRaises(ValueError):evaluate(native)

if __name__=='__main__':unittest.main()
