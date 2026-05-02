"""
The module CHILDES_age implements theage notation of CHILDES,
see MacWhinney https://talkbank.org/0info/manuals/CHAT.pdf , p 33.

It is important to use the correct format for the Target_Child’s age. This field uses the
form years;months.days as in 2;11.17 for 2 years, 11 months, and 17 days. The fields for
the months and days should always have two places. Using this format is important when
it comes to ordering data by age in spreadsheet systems such as Excel. This often means
that you need to add leading zeroes, as in 2;05.06 and 5;09.01. However, you do not need
to add any leading zeroes before the years. If you do not know the child's age in days, you
can simply use years and months, as in 6;04. with a period after the months. If you do not
know the months, you can use the form 6; with the semicolon after the years. If you only
know the child’s birthdate and the date of the transcript, you can use the DATES program
to compute the child’s age.



We allow single digit representations of months and days as input, although a two-digit representation is required
 """

from dataclasses import dataclass
import re
from sastadev.conf import settings
from sastadev.stringfunctions import lpad
from typing import Optional


vbar = '|'

days = [str(el) for el in list(range(32))] + [lpad(str(el), 2) for el in range(10)]
months = [str(el) for el in list(range(12))] + [lpad(str(el),2) for el in range(10)]

CHILDES_day_pattern = rf'\.(?:({vbar.join(days)})?)'

CHILDES_month_pattern = rf'(?:({vbar.join(months)}))'

CHILDES_age_pattern = rf'^(\d+);(?:{CHILDES_month_pattern}(?:{CHILDES_day_pattern})?)?$'

CHILDES_age_re = re.compile(CHILDES_age_pattern)

@dataclass
class CHILDESAge():
    years: int
    months: int
    days: int

    def __eq__(self, other):
        return self.years == other.years and self.months == other.months and self.days == other.days

    def __gt__(self, other):
        return (self.years, self.months, self.days) > (other.years, other.months, other.days)

    def __ge__(self, other):
        return (self.years, self.months, self.days) >= (other.years, other.months, other.days)

    def __repr__(self):
        if self.months == 0:
            mstr = ';'
        else:
            mstr= f';{lpad(str(self.months),2)}'

        if self.days == 0:
            dstr = '.'
        else:
            dstr = f'.{lpad(str(self.days), 2)}'
        result = f'{self.years}{mstr}{dstr}'
        return result


def childes_age_from_string(s: str) -> Optional[CHILDESAge]:
    match = CHILDES_age_re.match(s)
    if match is not None:
        years = int(match.group(1))
        months = int(match.group(2)) if match.group(2) else 0
        days = int(match.group(3)) if match.group(3) else 0
        result = CHILDESAge(years, months, days)
        return result
    else:
        settings.LOGGER.error(f'Invalid CHILDES age string: {s}')
        return None

def normalise_age(age: str) -> str:
    ch_age = childes_age_from_string(age)
    if ch_age is None:
        result = ch_age
    else:
        result = str(ch_age)
    return result

def month_diff(age1 :str, age2:str) -> int:
    ch_age1 = childes_age_from_string(age1)
    ch_age2 = childes_age_from_string(age2)
    months1 = 12 * ch_age1.years + ch_age1.months
    months2 = 12 * ch_age2.years + ch_age2.months
    result = months1 - months2
    return result

ok= 'ok'
acceptable = 'acceptable'
no = 'no'

ok_test_strings = ['3;', '3;04.', '3;04.03' ]
acceptable_teststrings = ['3;04', '3;4.', '3;4.3' ]
no_test_strings = ['3', '3;13.05', '3.12', '3;12.32']

teststring_pairs = ([(age, ok) for age in ok_test_strings] +
                    [(age, acceptable) for age in acceptable_teststrings] + [] +
                    [(age, no) for age in no_test_strings])
def tryme():
    verbose = True
    cc1 = CHILDESAge(years=2, months=10, days=31)
    print(cc1)
    for age, status in teststring_pairs:
        norm_age = normalise_age(age)
        if norm_age != age:
            norm_age_str = f' (normalised: {norm_age})'
        else:
            norm_age_str = ''

        try:
            cc = childes_age_from_string(age)
        except ValueError as e:
            if status != no:
                print(f'NO: {age} is well-formed but not recognized')
            elif verbose:
                print(f'OK: {age} is ill-formed and not recognized')
        else:
            if status not in {acceptable, ok}:
                print(f'NO: {age}{norm_age_str} is ill-formed but recognized')
            elif verbose:
                print(f'OK: {age}{norm_age_str} is {'well-formed' if status == ok else acceptable} and recognized')


    junk = 0


if __name__ == '__main__':
    tryme()



