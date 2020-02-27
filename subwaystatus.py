from dataclasses import dataclass, field
from typing import Dict, List
import datetime
import dateutil.parser
import distutils
import glob
import requests
import os
import untangle


def duration_str(duration):
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)

    if h > 1:
        return f'{h}h {m}m'
    else:
        return f'{m}m'


@dataclass
class ImpactedLine:
    code: str  # Use a the line construct from the stations package
    direction: str  # '0' or '1' for now, improve at some point


@dataclass
class SituationReport:
    summary: str
    description: str
    long_description: str
    #  these times end up being the first and last time a report is
    #  seen in the feed
    starttime: str
    endtime: str
    impacted_lines: List[ImpactedLine] = field(default_factory=list)


@dataclass
class Situation:
    situation_number: str
    planned: bool
    starttime: str  # time
    endtime: str  # time
    _reports: List[SituationReport] = field(default_factory=list)

    def add_report(self, report: SituationReport):
        """ only adds the report if it's unique """
        if len(self._reports) == 0:
            self._reports.append(report)
        else:
            most_recent_report = self._reports[-1]
            #  More thorough comparision
            if most_recent_report.summary != report.summary:
                self._reports.append(report)
            else:
                most_recent_report.endtime = report.endtime

    def close(self):
        self.endtime = self._reports[-1].endtime


class SituationParser:
    """ Give the SituationParser a sequence of xml files from the MTA
        and it will do some nice analysis """

    active_situations: [str]
    situations_by_number: Dict[str, Situation]
    all_situations: [Situation]

    def __init__(self):
        self.all_situations = []
        self.situations_by_number = {}
        self.active_situations = {}

    def process_xml(self, xml):
        """ """
        root = untangle.parse(xml)

        sitcount = len(
            root.Siri.ServiceDelivery.SituationExchangeDelivery.Situations)

        timestamp = root.Siri.ServiceDelivery.ResponseTimestamp.cdata

        new_active_situations = []

        if sitcount > 0:
            for situation_element in (root.Siri.
                                      ServiceDelivery.
                                      SituationExchangeDelivery.
                                      Situations.
                                      PtSituationElement):
                situation_number = (
                    situation_element.SituationNumber.cdata.strip()
                )

                if situation_number in self.situations_by_number:
                    situation = self.situations_by_number[situation_number]
                else:
                    planned = bool(distutils.util.strtobool(
                        situation_element.Planned.cdata.strip()))
                    if planned:
                        continue
                    situation = Situation(
                        situation_number,
                        planned,
                        timestamp,
                        '')
                    self.situations_by_number[situation_number] = situation
                    self.all_situations.append(situation)

                new_active_situations.append(situation_number)

                report = SituationReport(
                    situation_element.Summary.cdata.strip(),
                    situation_element.Description.cdata.strip(),
                    situation_element.LongDescription.cdata.strip(),
                    timestamp,
                    timestamp
                )
                for journey in (situation_element.
                                Affects.
                                VehicleJourneys.
                                AffectedVehicleJourney):
                    report.impacted_lines.append(
                        ImpactedLine(journey.LineRef.cdata.strip(),
                                     journey.DirectionRef.cdata.strip())
                    )

                situation.add_report(report)

        #  close up situations that are over (i.e. they were in the last
        #  xml, but not in this one
        for situation_number in self.active_situations:
            if situation_number not in new_active_situations:
                self.situations_by_number[situation_number].close()

        self.active_situations = new_active_situations

    def print_stats(self):
        print(f'Total situations: {len(self.all_situations)}')
        print('----------')
        for situation in self.all_situations:
            print(f'{situation.situation_number}')
            #  TODO this should be much better
            if situation.endtime:
                duration = (
                    dateutil.parser.parse(situation.endtime) -
                    dateutil.parser.parse(situation.starttime)
                )
            else:
                starttimestamp = dateutil.parser.parse(situation.starttime)
                tz = starttimestamp.tzinfo
                duration = (
                    datetime.datetime.now(tz) -
                    starttimestamp
                )
            print(duration_str(duration.seconds))

            print(f'{situation.starttime}  /  {situation.endtime}')
            for report in situation._reports:
                print(f'\t{report.summary}')
            print()


def get_current_situations():
    """  the current status from the MTA feed """
    # TODO some error handling
    rawresponse = requests.get(
        'http://web.mta.info/status/ServiceStatusSubway.xml'
    ).text
    return get_situations_from_xml(rawresponse)


def get_situations_from_xml(text):
    """ gets all the situations from an MTA xml file """
    situations = []
    root = untangle.parse(text)

    sitcount = len(
        root.Siri.ServiceDelivery.SituationExchangeDelivery.Situations)
    if sitcount == 0:
        return situations

    timestamp = root.Siri.ServiceDelivery.ResponseTimestamp.cdata

    for situation in (root.Siri.
                      ServiceDelivery.
                      SituationExchangeDelivery.
                      Situations.
                      PtSituationElement):
        situation_number = situation.SituationNumber.cdata.strip()
        planned = bool(distutils.util.strtobool(
            situation.Planned.cdata.strip()))
        # this doesn't seem to be right
        # starttime = situation.CreationTime.cdata.strip()
        starttime = timestamp
        endtime = ''  # we'll infer this later

        s = Situation(
            situation_number,
            planned,
            starttime,
            endtime
        )

        report = SituationReport(
            situation.Summary.cdata.strip(),
            situation.Description.cdata.strip(),
            situation.LongDescription.cdata.strip(),
            timestamp,
            timestamp
        )
        for journey in (situation.
                        Affects.
                        VehicleJourneys.
                        AffectedVehicleJourney):
            report.impacted_lines.append(
                ImpactedLine(journey.LineRef.cdata.strip(),
                             journey.DirectionRef.cdata.strip())
            )

        s.add_report(report)

        situations.append(s)

    return situations


def print_situations(situations):
    for situation in situations:
        print('{}\t{}\t{}'.format(
            situation.situation_number,
            situation.planned,
            situation.starttime))

        for report in situation._reports:
            print('\t{}'.format(report.summary))
            print('\t{}'.format(report.starttime))
            for line in report.impacted_lines:
                print('\t\t{}\t{}'.format(line.code, line.direction))

        print('\n')


parser = SituationParser()

os.chdir('rollingdata')
for filename in sorted(glob.glob('status*.xml')):
    with open(filename, 'r') as f:
        xml = f.read()
        # more_situations = get_situations_from_xml(xml)
        # situations.extend(more_situations)a
        parser.process_xml(xml)

parser.print_stats()


#  Old school
print('---------')

print_situations(get_current_situations())
