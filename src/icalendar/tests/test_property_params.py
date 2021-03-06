# coding: utf-8

from . import unittest

from .. import vCalAddress, Calendar, Event, Parameters


class TestPropertyParams(unittest.TestCase):

    def test_property_params(self):
        # Property parameters with values containing a COLON character, a
        # SEMICOLON character or a COMMA character MUST be placed in quoted
        # text.
        cal_address = vCalAddress('mailto:john.doe@example.org')
        cal_address.params["CN"] = "Doe, John"
        ical = Calendar()
        ical.add('organizer', cal_address)

        ical_str = Calendar.to_ical(ical)
        exp_str = """BEGIN:VCALENDAR\r\nORGANIZER;CN="Doe, John":"""\
                  """mailto:john.doe@example.org\r\nEND:VCALENDAR\r\n"""

        self.assertEqual(ical_str, exp_str)

        # other way around: ensure the property parameters can be restored from
        # an icalendar string.
        ical2 = Calendar.from_ical(ical_str)
        self.assertEqual(ical2.get('ORGANIZER').params.get('CN'), 'Doe, John')

    def test_unicode_param(self):
        cal_address = vCalAddress('mailto:john.doe@example.org')
        cal_address.params["CN"] = "Джон Доу"
        vevent = Event()
        vevent['ORGANIZER'] = cal_address
        self.assertEqual(
            vevent.to_ical(),
            'BEGIN:VEVENT\r\n'
            'ORGANIZER;CN="Джон Доу":mailto:john.doe@example.org\r\n'
            'END:VEVENT\r\n'
        )
        self.assertEqual(vevent['ORGANIZER'].params['CN'], 'Джон Доу')

    def test_quoting(self):
        # not double-quoted
        self._test_quoting(u"Aramis", 'Aramis')
        # if a space is present - enclose in double quotes
        self._test_quoting(u"Aramis Alameda", '"Aramis Alameda"')
        # a single quote in parameter value - double quote the value
        self._test_quoting("Aramis d'Alameda", '"Aramis d\'Alameda"')
        # double quote is replaced with single quote
        self._test_quoting("Aramis d\"Alameda", '"Aramis d\'Alameda"')
        self._test_quoting(u"Арамис д'Аламеда", '"Арамис д\'Аламеда"')

    def _test_quoting(self, cn_param, cn_quoted):
        """
        @param cn_param: CN parameter value to test for quoting
        @param cn_quoted: expected quoted parameter in icalendar format
        """
        vevent = Event()
        attendee = vCalAddress('test@mail.com')
        attendee.params['CN'] = cn_param
        vevent.add('ATTENDEE', attendee)
        self.assertEqual(
            vevent.to_ical(),
            'BEGIN:VEVENT\r\nATTENDEE;CN=%s:test@mail.com\r\nEND:VEVENT\r\n'
            % cn_quoted
        )

    def test_escaping(self):
        # verify that escaped non safe chars are decoded correctly
        NON_SAFE_CHARS = ur',\;:'
        for char in NON_SAFE_CHARS:
            cn_escaped = ur"Society\%s 2014" % char
            cn_decoded = ur"Society%s 2014" % char
            vevent = Event.from_ical(
                u'BEGIN:VEVENT\r\n'
                u'ORGANIZER;CN=%s:that\r\n'
                u'END:VEVENT\r\n' % cn_escaped
            )
            self.assertEqual(vevent['ORGANIZER'].params['CN'], cn_decoded)

        vevent = Event.from_ical(
            'BEGIN:VEVENT\r\n'
            'ORGANIZER;CN=that\\, that\\; %th%%at%\\\\ that\\:'
            ':это\\, то\\; that\\\\ %th%%at%\\:\r\n'
            'END:VEVENT\r\n'
        )
        self.assertEqual(
            vevent['ORGANIZER'].params['CN'],
            r'that, that; %th%%at%\ that:'
        )
        self.assertEqual(
            vevent['ORGANIZER'].to_ical(),
            r'это, то; that\ %th%%at%:'
        )

    def test_parameters_class(self):

        # Simple parameter:value pair
        p = Parameters(parameter1='Value1')
        self.assertEqual(p.to_ical(), 'PARAMETER1=Value1')

        # keys are converted to upper
        self.assertEqual(p.keys(), ['PARAMETER1'])

        # Parameters are case insensitive
        self.assertEqual(p['parameter1'], 'Value1')
        self.assertEqual(p['PARAMETER1'], 'Value1')

        # Parameter with list of values must be seperated by comma
        p = Parameters({'parameter1': ['Value1', 'Value2']})
        self.assertEqual(p.to_ical(), 'PARAMETER1=Value1,Value2')

        # Multiple parameters must be seperated by a semicolon
        p = Parameters({'RSVP': 'TRUE', 'ROLE': 'REQ-PARTICIPANT'})
        self.assertEqual(p.to_ical(), 'ROLE=REQ-PARTICIPANT;RSVP=TRUE')

        # Parameter values containing ',;:' must be double quoted
        p = Parameters({'ALTREP': 'http://www.wiz.org'})
        self.assertEqual(p.to_ical(), 'ALTREP="http://www.wiz.org"')

        # list items must be quoted seperately
        p = Parameters({'MEMBER': ['MAILTO:projectA@host.com',
                                   'MAILTO:projectB@host.com']})
        self.assertEqual(
            p.to_ical(),
            'MEMBER="MAILTO:projectA@host.com","MAILTO:projectB@host.com"'
        )

        # Now the whole sheebang
        p = Parameters({'parameter1': 'Value1',
                        'parameter2': ['Value2', 'Value3'],
                        'ALTREP': ['http://www.wiz.org', 'value4']})
        self.assertEqual(
            p.to_ical(),
            ('ALTREP="http://www.wiz.org",value4;PARAMETER1=Value1;'
             'PARAMETER2=Value2,Value3')
        )

        # We can also parse parameter strings
        self.assertEqual(
            Parameters.from_ical('PARAMETER1=Value 1;param2=Value 2'),
            Parameters({'PARAMETER1': 'Value 1', 'PARAM2': 'Value 2'})
        )

        # Including empty strings
        self.assertEqual(Parameters.from_ical('param='),
                         Parameters({'PARAM': ''}))

        # We can also parse parameter strings
        self.assertEqual(
            Parameters.from_ical(
                'MEMBER="MAILTO:projectA@host.com","MAILTO:projectB@host.com"'
            ),
            Parameters({'MEMBER': ['MAILTO:projectA@host.com',
                                   'MAILTO:projectB@host.com']})
        )

        # We can also parse parameter strings
        self.assertEqual(
            Parameters.from_ical('ALTREP="http://www.wiz.org",value4;'
                                 'PARAMETER1=Value1;PARAMETER2=Value2,Value3'),
            Parameters({'PARAMETER1': 'Value1',
                        'ALTREP': ['http://www.wiz.org', 'value4'],
                        'PARAMETER2': ['Value2', 'Value3']})
        )
