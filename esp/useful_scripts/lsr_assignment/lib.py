path_to_esp = '/esp/esp/'

import sys
sys.path += [path_to_esp, path_to_esp + 'esp/']

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'esp.settings'

import random

from esp.cal.models import Event
from esp.users.models import User, ESPUser
from esp.program.models import Program, ClassSection, StudentRegistration, RegistrationType


################################
# Global Settings and Thingies #
################################

# Priority and Interested registration types for use with assignments.
priority_type = 'Priority/1'
interested_type = 'Interested'
enrolled_type = 'Enrolled'

# Numerical parameters for assigning students a score for getting into classes.
onestar = 1
twostar = 1.1
twostarstar = 1.05

# Range for random number generation.  A random number will be generated
# in this range, and multiplied by the value, for some randomness.
rangemin = 0.7
rangesize = 0.6

# The program used for these scripts.
# ID 65 = Splash 2010.
program = Program.objects.get(id=65)

# Lunch hours, for checking whether a student has lunch free.
satlunch = Event.objects.filter(id__in=[495,496])
sunlunch = Event.objects.filter(id__in=[497,498])

# The wiggle room factor for the class capacity, to leave a space for
# those classes that didn't fill up from priority.  Set to 10% for now.
# This variable is the multiplicative factor.
# Seems we're not currently using this right now.
wiggle = 0.9

def class_cap(cls):
    """
    Determine the class capacity of a class as calculated by whatever
    it is we're using to calculate it for these classes.
    cls -- the class section in question.
    """
    return cls.parent_class.class_size_optimal

def capacity_star(cls):
    """ 
    For now, we're not using this, but if we ever want to use a capacity
    that's less than the full capacity we can use this or something.
    """
    return class_cap(cls)

####################
# Helper Functions #
####################

def lunch_free(user, lunchtimes):
    registrations = StudentRegistration.valid_objects().filter(user=user, section__parent_class__parent_program=program, relationship__name=enrolled_type).values('section').distinct()
    secids = [reg['section'] for reg in registrations]

    return ClassSection.objects.filter(id__in=secids, meeting_times__in=lunchtimes).count() == 0

# TODO(rye): Add a mechanism for lunch, with some helper functions to ensure lunch.
def try_add(user, cls):
    """
    Try to add this student to the class.  First checks whether the student
    can add the class given their current schedule and grade level,
    then assigns them to the class.

    Returns True if assignment was successful, False otherwise.
    """
    # First, check if this class runs over lunch, and if so, make sure
    # the student actually has lunch free.
    if cls.meeting_times.filter(id__in=satlunch).count() > 0:
        if not lunch_free(user, satlunch):
            return False
    if cls.meeting_times.filter(id__in=sunlunch).count() > 0:
        if not lunch_free(user, sunlunch):
            return False

    # Now we've worked out any potential lunch conflicts.
    # Check if this user can actually add this section (and has no conflicts).
    error = cls.cannotAdd(user)
    if not error:
        # If there are no conflicts, check the parent class for permissions.
        error = cls.parent_class.cannotAdd(user)

    # If there's still no errors, proceed with registering the student.
    if not error:
        success = cls.preregister_student(user, prereg_verb='Enrolled')
        return success
    else:
        return False

def priority_lottery_val(user):
    """
    Calculate the probability of this student getting to the front of the
    list for getting assigned into a priority class.  Depends only
    on how many classes they've gotten in the past (more likely if fewer).

    Assume here that the only classes they've gotten into so far 
    are priority classes.  This is true given when this will be used,
    but makes it not a general function.
    """
    priority_ids = [r['section'] for r in StudentRegistration.valid_objects().filter(user=user, section__parent_class__parent_program=program, relationship__name=priority_type).values('section').distinct()]
    reged_classes_count = StudentRegistration.valid_objects().filter(user=user, section__id__in=priority_ids, relationship__name=enrolled_type).values('section').distinct().count()

    # Randomly generate a number in the range specified above.
    retval = (random.random() * rangesize) + rangemin

    if reged_classes_count > 0:
        retval *= onestar / (reged_classes_count * twostar)
    else: 
        retval *= onestar

    return retval

def interested_lottery_val(user):
    """ 
    Calculate the probability value for this user in the lottery.
    Based on how many of their priority classes the user has already gotten
    into, and how many of their interested classes the user got into.
    """

    interested_ids = [r['section'] for r in StudentRegistration.valid_objects().filter(user=user, section__parent_class__parent_program=program, relationship__name=interested_type).values('section').distinct()]
    interested_count = StudentRegistration.valid_objects().filter(user=user, section__id__in=interested_ids, relationship__name=enrolled_type).values('section').distinct().count()

    # The randomizing factor already exists in the returned value of this
    # function, so what we do here is just multiply it by more factors.
    retval = priority_lottery_val(user)

    if interested_count > 0:
        retval *= 1 / (interested_count * twostarstar)

    return retval

# Getter functions for the user, priority_value thingy
def bundle_priority(user):
    return (user, priority_lottery_val(user))

def bundle_interested(user):
    return (user, interested_lottery_val(user))

def get_user(bundle):
    return bundle[0]

def get_val(bundle):
    return bundle[1]


################################
# Lottery Assignment Functions #
################################

def assign_priorities():
    """
    Assign people to their priority classes.  At the end of this function
    every student will be assigned to the classes of their priorities that
    they get into.

    Phase one:
    Loop through all class sections in this program, and for each of
    these if the number of priority flags is less than the class
    capacity, enroll everybody in the class (who can be in the class).

    Phase two:
    Go through all the class sections that we didn't manage to assign
    folks to in phase one (because there were too many people who
    marked it priority), and do a preference-based lottery for the
    people who have marked this class.    
    """
    all_secs = program.sections().filter(status__gt=0)

    # These will be lists of tuples: (sec, priority-flags)
    phase1_secs = []
    phase2_secs = []

    # Division of sections into phase 1 and phase 2 sections
    for sec in all_secs:
        # First get how many students marked this as their first choice;
        # if it's greater than the class capacity, then don't deal with
        # this now.
        # Because there are duplicate registrations for each, just get the
        # distinct users who marked this class as priority.
        priority_regs = StudentRegistration.valid_objects().filter(section=sec, relationship__name=priority_type).values('user').distinct()
        if (priority_regs.count() > class_cap(sec)):
            phase2_secs.append((sec, priority_regs))
        else: 
            phase1_secs.append((sec, priority_regs))

    # Handle the phase 1 sections
    for sec, priority in phase1_secs:
        print "== Adding priority students to " + sec.emailcode() + ": " + sec.title() + " =="

        # Loop through all classes where priority flags is less than capacity.
        # Try to register each student for the class; we don't care if
        # it fails, because no one's competing for the spots.
        for reg in priority:
            thisuser = ESPUser.objects.get(id=reg['user'])
            success = try_add(thisuser, sec)
            if success:
                print thisuser.name() + " (" + thisuser.username + ")"

    # Handle the phase 2 sections
    for sec, priority in phase2_secs:
        print "== Adding priority students to " + sec.emailcode() + ": " + sec.title() + " =="

        # We want to lottery students by ordering them in some way,
        # giving preference to the students who have so far gotten fewer
        # of their priority classes.  Once the order is established,
        # try adding students until the number of successes is the capacity
        # of the class.
        #
        # Students are likely to have a higher priority reg value when they
        # have fewer classes so far, so sort the students by decreasing reg value.
        users_by_priority = sorted([bundle_priority(ESPUser.objects.get(id=r['user'])) for r in priority], key=get_val, reverse=True)

        # Now register the students in the order they got sorted.
        # Note: this could alternatively be done by trying to add each user in
        # the list of users who ranked this as priority; they'll all start
        # failing after the class is full. TODO(rye): Figure out if this is
        # actually the way we want to do things.
        registered_count = 0
        cur_index = 0
        while (registered_count < class_cap(sec)) and (cur_index < len(users_by_priority)):
            thisuser = get_user(users_by_priority[cur_index])
            success = try_add(thisuser, sec)
            cur_index += 1

            # If we succeeded, make sure to add one to the registered count.
            if success:
                print thisuser.name() + " (" + thisuser.username + ")"
                registered_count += 1


def screwed_sweep_p1_printout():
    """
    Print out the percentage that each student got, of the priority
    classes that they marked, in order of increasing percentage.
    Also print out, for easy reference, the number of priority classes they
    got out of the total chosen.
    """
    def classes_cnt(user):
        classescnt = StudentRegistration.valid_objects().filter(section__parent_class__parent_program=program, user=user, relationship__name=enrolled_type).values('section').distinct().count()
        pcnt = StudentRegistration.valid_objects().filter(section__parent_class__parent_program=program, user=user, relationship__name=priority_type).values('section').distinct().count()
        return (classescnt, pcnt)

    def pclasses_pct(user):
        counts = classes_cnt(user)
        if counts[1] != 0:
            return 100*(counts[0]/(counts[1]*1.0))
        else: return 0

    users = sorted(program.students()['lotteried_students'], key=pclasses_pct)
    for user in users:
        print user.name(), ":", pclasses_pct(user), "(" + str(classes_cnt(user)[0]) + "/" + str(classes_cnt(user)[1]) + ")"    
        

def assign_interesteds():
    """
    Go through all sections that still have space in them, and assign them
    some of the students who were interested in the class.  Start with the
    class with the fewest "interested" markings.

    Phase 4:
    For any classes whose count of interested kids is less than their capacity,
    just fill them up right away.  All other sections are filled in the order
    of number of people interested (increasing).

    Phase 5:
    Similar to phase 2.  Go through all class sections where we didn't assign
    people because there was a conflict over capacity*
    """
    # Function to return the number of people who flagged this class as
    # something they're interested in.  Used for sorting the sections.
    # Actually, this key is changing to a division.
    def interested_count(sec):
        count = StudentRegistration.valid_objects.filter(section=sec, relationship__name=interested_type).values('user').distinct().count()
        return count/(1.0*class_cap(sec))

    # Filter out all the classes that we filled up in the priority reg stage
    # so we don't worry about them anymore in this stage.
    nonempty_secs = [sec for sec in program.sections().filter(status__gt=0) if not sec.isFull()]

    # Now sort the classes by fewest number of people interested.
    sorted_secs = sorted(nonempty_secs, interested_count)

    # In the order of the classes that have the fewest interested
    # people in it (currently, ratio'd with how large they are), 
    # fill up the classes by lottery.
    for sec in sorted_secs:
        print "== Adding interested students to " + sec.emailcode() + ": " + sec.title() + " =="

        # Same procedure as in the case of priority registrations.
        interesteds = StudentRegistration.valid_objects().filter(section=sec, relationship__name=interested_type).values('user').distinct()
        users_by_val = sorted([bundle_interested(ESPUser.objects.get(id=r['user'])) for r in interesteds], key=get_val, reverse=True)

        # It's easier to, instad of counting, just fill the class till it's
        # full.  If we change to actually using capacity*, this will need to
        # change to have logic similar to the priority registration.
        cur_index = 0
        while not (sec.isFull()):
            thisuser = get_user(users_by_val[cur_index])
            success = try_add(thisuser, sec)
            cur_index += 1

            # If we succeeded, make sure to add one to the registered count.
            if success:
                print thisuser.name() + " (" + thisuser.username + ")"
