#!/usr/bin/env python2

import datetime
import time
import re
import string
import os
import os.path
import sys

DEFAULT_SCHEDULE='3.14.schedule'

class GnomeReleaseEvent:
    definitions = {}
    categories = {
        "release": {
            "prio": 1,
            "summary_template": 'GNOME $version $detail release',
            'wiki_template': 'GNOME $version $detail release',
            'description_template': 'GNOME $version $detail release',
        },
        "tarball": {
            "prio": 2,
            "automail": True,
            'summary_template': 'GNOME $version $detail tarballs due',
            "wiki_template": 'GNOME $version $detail tarballs due',
            "description_template": """Tarballs are due on $date before 23:59 UTC for the GNOME
$version $detail release, which will be delivered on Wednesday.
Modules which were proposed for inclusion should try to follow the unstable
schedule so everyone can test them.

Please make sure that your tarballs will be uploaded before Monday 23:59
UTC: tarballs uploaded later than that will probably be too late to get
in $version. If you are not able to make a tarball before this deadline or
if you think you'll be late, please send a mail to the release team and
we'll find someone to roll the tarball for you!""",
        },
        "freeze": {
            "prio": 3,
            "automail": True,
            "summary_template": {
                'feature': 'Feature and Module Freeze',
                'the-freeze': 'API/ABI, UI and Feature Addition Freeze; String Change Announcement Period',
                'string': 'String Freeze',
                'hard-code': 'Hard Code Freeze',
                'hard-code-end': 'Hard Code Freeze ends',
                # not used anymore since 3.3:
                'feature2': 'Feature Addition Freeze',
                'string-announcement': 'String Change Announcement Period',
                'ui-announcement': 'UI Change Announcement Period',
                'api': 'API/ABI Freeze',
                'module': 'Module Freeze',
                'ui': 'UI Freeze'
            },
            "wiki_template": {
                'feature': '[[ReleasePlanning/Freezes|Feature and Module Freeze]]: new system-wide functionality and modules are chosen now.',
                'the-freeze': 'The Freeze: [[ReleasePlanning/Freezes|UI Freeze]]: No UI changes may be made without approval from the [[https://mail.gnome.org/mailman/listinfo/release-team|release-team]] and notification to [[https://mail.gnome.org/mailman/listinfo/gnome-doc-list|gnome-doc-list@]]; [[ReleasePlanning/Freezes|Feature Freeze]]: new functionality is implemented now; [[ReleasePlanning/Freezes|API/ABI Freeze]] for $unstable.x: Developer APIs should be frozen at this point; String Change Announcement Period: All string changes must be announced to both [[https://mail.gnome.org/mailman/listinfo/gnome-i18n|gnome-i18n@]] and [[https://mail.gnome.org/mailman/listinfo/gnome-doc-list|gnome-doc-list@]].',
                'string': '[[ReleasePlanning/Freezes|String Freeze]]: no string changes may be made without confirmation from the l10n team ([[https://mail.gnome.org/mailman/listinfo/gnome-i18n|gnome-i18n@]]) and notification to both the release team and the GDP ([[https://mail.gnome.org/mailman/listinfo/gnome-doc-list|gnome-doc-list@]]).',
                'hard-code': '[[ReleasePlanning/Freezes|Hard Code Freeze]]: no source code changes can be made without approval from the [[https://mail.gnome.org/mailman/listinfo/release-team|release-team]]. Translation and documentation can continue.',
                'hard-code-end': 'Hard Code Freeze ends, but other freezes remain in effect for the stable branch.',
                # 'string-announcement' merged into 'the-freeze' for 3.3
                'string-announcement': 'String Change Announcement Period: All string changes must be announced to both [[https://mail.gnome.org/mailman/listinfo/gnome-i18n|gnome-i18n@]] and [[https://mail.gnome.org/mailman/listinfo/gnome-doc-list|gnome-doc-list@]].',
                # 'ui-announcement' not used anymore since 3.3
                'ui-announcement': 'UI Change Announcement Period: All user interface changes must be announced to [[https://mail.gnome.org/mailman/listinfo/gnome-doc-list|gnome-doc-list@]].',
                # 'api' merged into 'the-freeze' for 3.3
                'api': '[[ReleasePlanning/Freezes|API/ABI Freeze]] for $unstable.x: developer APIs should be frozen at this point.',
                # 'module' not used anymore since 3.1, replaced by 'feature'
                'module': '[[ReleasePlanning/Freezes|Module Freeze]]: new modules are chosen now.',
                # 'feature2' merged into 'the-freeze' for 3.3
                'feature2': '[[ReleasePlanning/Freezes|Feature Freeze]]: new functionality is implemented now.',
                # 'ui' merged into 'the-freeze' for 3.3
                'ui': '[[ReleasePlanning/Freezes|UI Freeze]]: No UI changes may be made without approval from the [[https://mail.gnome.org/mailman/listinfo/release-team|release-team]] and notification to the GDP ([[https://mail.gnome.org/mailman/listinfo/gnome-doc-list|gnome-doc-list@]])'
            },
            'description_template': {
                'string-announcement': 'String Change Announcement Period',
                'ui-announcement': 'UI Change Announcement Period',
                'api': """No API or ABI changes should be made in the platform libraries. For instance, no new functions, no changed function signatures or struct fields.

This provides a stable development platform for the rest of the schedule.

There should usually be a "Slushy" API/ABI Freeze before the Hard API/ABI Freeze, to encourage developers to think about API problems while they have a chance to correct them.

API freeze is not required for non-platform libraries, but is recommended.""",
                'feature': """Desktop and platform release module additions are finalised, major feature additions are listed. No new modules or features will be accepted for this release period. "Feature" should be interpreted as "Functionality" or "Ability". Bug fixes of existing features are not affected.

This allows developers to concentrate on refining the new features instead of adding yet more functionality.""",
                'ui': """No UI changes may be made at all without confirmation from the release team and notification to the documentation team.""",
                'string': """No string changes may be made without confirmation from the i18n team and notification to release team, translation team, and documentation team.
From this point, developers can concentrate on stability and bug-fixing. Translators can work without worrying that the original English strings will change, and documentation writers can take accurate screenshots.
For the string freezes explained, and to see which kind of changes are not covered by freeze rules, check https://wiki.gnome.org/TranslationProject/HandlingStringFreezes. """,
                'hard-code': """This is a late freeze to avoids sudden last-minute accidents which could risk the stability that should have been reached at this point. No source code changes are allowed without approval from the release team, but translation and documentation should continue. Simple build fixes are, of course, allowed without asking. """,
                'hard-code-end': """Hard Code Freeze ends, but other freezes remain in effect for the stable branch."""
            },
        },
        "modules": {
            "prio": 4,
            "automail": True,
            "summary_template": {
                'proposals-start': 'New module proposal start',
                'proposals-end': 'New module proposal end',
                'discussion': 'Module inclusion discussion heats up',
                'decision': 'Release Team decides on new modules'
            },
            "wiki_template": {
                'proposals-start': 'Start of new module proposals period for $newstable',
                'proposals-end': 'End of new module proposals period for $newstable',
                'discussion': 'Module proposals discussion heats up.',
                'decision': '[[https://mail.gnome.org/mailman/listinfo/release-team|Release Team]] meets about new module proposals for $newstable with community input up to this point.'
            },
            'description_template': {
                'proposals-start': 'New module proposal start',
                'proposals-end': 'New module proposal end',
                'discussion': 'Module proposals discussion heats up',
                'decision': 'Release Team decides on new modules'
            },
        },
        "features": {
            "prio": 5,
            "automail": True,
            "summary_template": {
                'proposals-start': 'New feature proposals period start',
                'proposals-end': 'New feature proposals period end',
                'discussion': 'Feature proposals discussion heats up',
                'decision': 'Release Team decides on new features',
                'proposals-start-next': 'New feature proposals period start'
            },
            "wiki_template": {
                'proposals-start': 'Start of new feature proposals period for $newstable',
                'proposals-end': 'End of new feature proposals period for $newstable',
                'discussion': 'Feature proposals discussion heats up.',
                'decision': '[[https://mail.gnome.org/mailman/listinfo/release-team|Release Team]] meets about new feature proposals for $newstable with community input up to this point.',
                'proposals-start-next': 'Start of new feature proposals period for $nextnewstable'
            },
            'description_template': {
                'proposals-start': 'New feature proposals period start',
                'proposals-end': 'New feature proposals period end',
                'discussion': 'Feature proposals discussion heats up',
                'decision': 'Release Team decides on new features',
                'proposals-start-next': 'New feature proposals period start'
            },
        },
        "task": {
            "prio": 6,
            "automail": True,
            "summary_template": {
                'api-doc': 'New APIs must be fully documented',
                'release-notes-start': 'Writing of release notes begins'
            },
            "wiki_template": {
                'api-doc': '[[https://wiki.gnome.org/ReleasePlanning/ModuleRequirements/Platform#head-2a21facd40d5bf2d73f088cd355aa98b6a2458df|New APIs must be fully documented]]',
                'release-notes-start': '[[https://wiki.gnome.org/ReleaseNotes|Writing of release notes begins]]'
            },
            'description_template': {
                'api-doc': 'New APIs must be fully documented',
                'release-notes-start': 'Writing of release notes begins'
            }
        },
        "conference": {
            "prio": 7,
            "summary_template": '$detail conference',
            "wiki_template": '$detail conference',
        },
        "hackfest": {
            "prio": 8,
            "summary_template": '$detail hackfest',
            "wiki_template": '$detail hackfest',
        },
    }

    def __init__ (self, date, week, category, detail, version=None, assignee=None):
        self.date = date
        self.isoweek = (date.isocalendar()[0] * 100) + date.isocalendar()[1]
        self.rel_week = week
        self.category = category
        self.detail = detail
        self.version = version
        self.assignee = assignee
        self.prio = None
        self.automail = False
        self.wiki_template = None
        self.description_template = None
        self.summary_template = None

        for name, value in self.categories[category].iteritems():
            setattr(self, name, value)

    def __getitem__(self, item):
        """Allows the GnomeReleaseEvent class to be used in a string.Template"""
        if hasattr(self, item):
            return getattr(self, item)
        else:
            return self.__class__.definitions[item]

    def __repr__(self):
        v = self.version
        if v is None:
            v = ''
        else:
            v = ' ' + v
        return "<%s: %s %s %s%s>" % (self.__class__, self.date, self.category, self.detail, v)

    @property
    def wiki_text(self):
        text = self.make_text(self.wiki_template)

        if text is None:
            return `self`
        else:
            return text

    @property
    def summary(self):
        text = self.make_text(self.summary_template)

        if text is None:
            return `self`
        else:
            return text

    @property
    def description(self):
        text = self.make_text(self.description_template)

        if text is None:
            return ""
        else:
            return text

    def make_text(self, predef):
        text = None

        if type(predef) == dict:
            text = predef.get(self.detail)
        elif type(predef) == str:
            text = predef

        if text is not None and '$' in text:
            text = string.Template(text).safe_substitute(self)

        return text

    def __cmp__ (self, other):
        return cmp(self.date, other.date) or cmp(self.prio, other.prio)

def find_date(year, week):
    guessed = datetime.date(year, 2, 1)
    (iso_y, iso_w, iso_d) = guessed.isocalendar()
    return guessed - datetime.timedelta((iso_d - 1) + (iso_w - week) * 7)

def line_input (file):
    for line in file:
        if line[-1] == '\n':
            yield line[:-1]
        else:
            yield line

def parse_file (filename=DEFAULT_SCHEDULE, cls=GnomeReleaseEvent):
    try:
        file = open(filename, 'r')
    except IOError:
        file = open(os.path.join(os.path.abspath(sys.path[0] or os.curdir), filename), 'r')

    events = []
    start = None

    definitions = cls.definitions

    for line in line_input(file):
        # ignore comments & empty lines
        if line == '' or line[0] == "#":
            continue

        if not ':' in line:
            print "Error: line '%s' is not parsable" % line[0:-1]
            return None

        info = [item.strip() for item in line.split(':')]

        if len(info) == 2:
            if info[0].lower() == 'yearweek':
                if start:
                    print "Error: more than one start date specified"
                    return None

                year = int(info[1][:4])
                week = int(info[1][-2:])
                if year < 2007 or year > 2020:
                    print "Error: %s is not a valid year for the start date" % year
                    return None
                if week > 54:
                    print "Error: %s is not a valid week for the start date" % week
                    return None
                start = find_date(year, week)
            else:
                definitions[info[0].lower()] = info[1]
            continue
        else:
            if not start or 'unstable' not in definitions or 'stable' not in definitions:
                print "Error: Need yearweek, stable and unstable definitions before line '%s'" % line[0:-1]
                return None

            if info[0].isdigit():
                week = int(info[0])
                if week < -10 or week > 53:
                    print "Error: %s is not a valid week for an event" % week
                    return None
                date = start + datetime.timedelta(week * 7)
            else:
                date = datetime.date(*(time.strptime(info[0], '%Y-%m-%d')[0:3]))
            category = info[1].lower()
            event = info[2]
            if category not in cls.categories:
                print "Error: %s is not a valid category for an event" % category
                return None

            # Expand event info
            version = None
            assignee = None
            if category == 'release' and '.' in event:
                if ' ' in event:
                    i = event.split(' ', 1)
                    event = i[0]
                    if i[1].strip():
                        assignee = i[1].strip()

                i = event.split('.', 1)
                if not '.' in i[1]:
                    event = i[0]
                    i[0] = definitions.get(i[0], definitions['unstable'])
                    version = '.'.join(i)
            if category == 'release' and version is None:
                print "Error: line '%s' is not parsable" % line[0:-1]
                return None

            if category == 'release':
                rel_event = cls(date, week, 'tarball', event, version, assignee)
                events.append (rel_event)
                date = date + datetime.timedelta(2)

            rel_event = cls(date, week, category, event, version, assignee)
            events.append (rel_event)
            continue

    file.close ()

    if not start:
        print "Error: empty data file"
        return None

    events.sort()

    return events

if __name__ == '__main__':
    d = datetime.date(1980,1,7)
    end = datetime.date(2020,1,1)
    adv = datetime.timedelta(7)
    while d < end:
        yw = d.isocalendar()[:2]
        dcalc = find_date(yw[0], yw[1])
        print yw, dcalc, d, "" if d == dcalc else "WRONG"

        d += adv
