
__author__    = "Individual contributors (see AUTHORS file)"
__date__      = "$DATE$"
__rev__       = "$REV$"
__license__   = "AGPL v.3"
__copyright__ = """
This file is part of the ESP Web Site
Copyright (c) 2007 by the individual contributors
  (see AUTHORS file)

The ESP Web Site is free software; you can redistribute it and/or
modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

Contact information:
MIT Educational Studies Program
  84 Massachusetts Ave W20-467, Cambridge, MA 02139
  Phone: 617-253-4882
  Email: esp-webmasters@mit.edu
Learning Unlimited, Inc.
  527 Franklin St, Cambridge, MA 02139
  Phone: 617-379-0178
  Email: web-team@lists.learningu.org
"""
from esp.qsd.views import qsd
from django.core.exceptions import PermissionDenied
from django.contrib.sites.models import Site
from esp.program.modules.base import LOGIN_URL
from django.contrib.auth import REDIRECT_FIELD_NAME
from esp.datatree.models import *
from esp.users.models import GetNodeOrNoBits, ESPUser, UserBit
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.template import loader
from esp.middleware.threadlocalrequest import AutoRequestContext as Context

#from icalendar import Calendar, Event as CalEvent, UTC

import datetime

from esp.web.models import NavBarCategory
from esp.web.util.main import render_to_response
from esp.web.views.navBar import makeNavBar
from esp.web.views.myesp import myesp_handlers
from esp.web.views.archives import archive_handlers
from esp.middleware import ESPError
from esp.web.forms.contact_form import ContactForm, email_addresses
from esp.tagdict.models import Tag

from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control
from django.core.mail import mail_admins

from django.views.decorators.csrf import csrf_exempt

from pprint import pprint

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


# get_callable might not actually be public API. Django's nice and well-documented like that.
def my_import(name):
    from django.core.urlresolvers import get_callable
    return get_callable(name)

def home(request):
    #   Get navbars corresponding to the 'home' category
    nav_category, created = NavBarCategory.objects.get_or_create(name='home')
    context = {'navbar_list': makeNavBar(None, GetNode('Q/Web'), '', nav_category)}
    return render_to_response('index.html', request, GetNode('Q/Web'), context)

@vary_on_headers('Cookie')
def myesp(request, module):
	""" Return page handled by myESP (generally, a user-specific page) """
	if myesp_handlers.has_key(module):
		return myesp_handlers[module](request, module)

	return render_to_response('users/construction', request, GetNode('Q/Web/myesp'), {})


@vary_on_headers('Cookie')
def redirect(request, url, subsection = None, filename = "", section_redirect_keys = {}, section_prefix_keys = {}, renderer = qsd ):
	""" Universal mapping function between urls.py entries and QSD pages

	Calls esp.qsd.views.qsd to actually get the QSD pages; we just find them
	"""

	if isinstance(renderer, basestring):
		renderer = my_import(renderer)
	
	if filename != "":
		url = url + "/" + filename

	tree_branch = section_redirect_keys[subsection]

	# URLs will be of the form "path/to/file.verb", or "path/to/file".
	# In the latter case, assume that verb = view
	# In either case, "path/to" is the tree path to the relevant page

	url_parts = url.split('/')
	url_address = url_parts.pop()

	url_address_parts = url_address.split('.')

	if len(url_address_parts) == 1: # We know the name; use the default verb
		qsd_name = url_address_parts[0]
		qsd_verb = 'read'
	elif len(url_address_parts) == 2: # We're given both pieces; hopefully that's all we're given (we're ignoring extra data here)
		qsd_name = url_address_parts[0]
		qsd_verb = url_address_parts[1]
	else: # In case someone breaks urls.py and "foo/.html" is allowed through
		raise Http404

	# If we have a subsection, descend into a node by that name
	target_node = url_parts

	# Get the node in question.  If it doesn't exist, deal with whether or not this user can create it.
	try:
		branch_name = 'Q/' + tree_branch
		if target_node:
			branch_name = branch_name + '/' + "/".join(target_node)
		branch = GetNodeOrNoBits(branch_name, user=request.user)
	except DataTree.NoSuchNodeException:
		raise ESPError(False), "Directory does not exist."
		#edit_link = request.path[:-5]+'.edit.html'
		#return render_to_response('qsd/qsd_nopage_edit.html', request, (branch, section), {'edit_link': edit_link})
	except PermissionDenied:
		raise Http404
		
	if url_parts:
		root_url = "/" + "/".join(url_parts) + "/" + qsd_name
	else:
		root_url = "/" + qsd_name


	section = ''
	if subsection == None:
		subsection_str = ''
	else:
		subsection_str = subsection + "/"
		root_url = "/" + subsection + root_url
		if section_prefix_keys.has_key(subsection):
			section = section_prefix_keys[subsection]
			qsd_name = section + ':' + qsd_name
	
	return renderer(request, branch, section, qsd_name, qsd_verb, root_url)
	
def program(request, tl, one, two, module, extra = None):
	""" Return program-specific pages """
        from esp.program.models import Program
        
	try:
		prog = Program.by_prog_inst(one, two) #DataTree.get_by_uri(treeItem)
	except Program.DoesNotExist:
		raise Http404("Program not found.")

        setattr(request, "program", prog)
        setattr(request, "tl", tl)
        if extra:
            setattr(request, "module", "%s/%s" % (module, extra))
        else:
            setattr(request, "module", module)
            
	from esp.program.modules.base import ProgramModuleObj
	newResponse = ProgramModuleObj.findModule(request, tl, one, two, module, extra, prog)

	if newResponse:
		return newResponse

	raise Http404

def classchangerequest(request, tl, one, two):
    from esp.program.models import Program, StudentAppResponse
    from esp.program.models.class_ import * 
        
    try:
        prog = Program.by_prog_inst(one, two) #DataTree.get_by_uri(treeItem)
    except Program.DoesNotExist:
        raise Http404("Program not found.")
    
    if tl != "learn":
        raise Http404

    if not request.user or not request.user.is_authenticated():
        return HttpResponseRedirect('%s?%s=%s' % (LOGIN_URL, REDIRECT_FIELD_NAME, quote(request.get_full_path())))

    if not request.user.isStudent() and not request.user.isAdmin(prog):
        allowed_student_types = Tag.getTag("allowed_student_types", prog, default='')
        matching_user_types = UserBit.valid_objects().filter(user=request.user, verb__parent=GetNode("V/Flags/UserRole"), verb__name__in=allowed_student_types.split(","))
        if not matching_user_types:
            return render_to_response('errors/program/notastudent.html', request, (prog, 'learn'), {})
    
    errorpage = 'errors/program/wronggrade.html'
    
    verb_override = GetNode('V/Flags/Registration/GradeOverride')
    cur_grade = request.user.getGrade(prog)
    if (not UserBit.UserHasPerms(user = request.user, qsc  = prog.anchor_id, verb = verb_override)) and (cur_grade != 0 and (cur_grade < prog.grade_min or \
                           cur_grade > prog.grade_max)):
        return render_to_response(errorpage, request, (prog, tl), {})

    setattr(request, "program", prog)
    setattr(request, "tl", tl)
    setattr(request, "module", "classchangerequest")

    from django import forms
    from datetime import datetime
    from esp.utils.scheduling import getRankInClass

    timeslots = prog.getTimeSlots()
    sections = prog.sections().filter(status=10)
    
    enrollments = dict([(timeslot, ClassSubject.objects.get(sections__studentregistration__relationship__name="Enrolled", sections__studentregistration__user=request.user, sections__meeting_times=timeslot, parent_program=prog, sections__studentregistration__end_date__gte=datetime.now())) for timeslot in timeslots])
    print enrollments
    sections_by_slot = dict([(timeslot,[section for section in sections if section.get_meeting_times()[0] == timeslot and section.parent_class.grade_min <= request.user.getGrade(prog) <= section.parent_class.grade_max and section.parent_class not in enrollments.values() and getRankInClass(request.user, section) in (5,10)]) for timeslot in timeslots])
    print sections_by_slot
    print getRankInClass(request.user, ClassSection.objects.get(parent_class__parent_program__pk=72, parent_class__anchor__friendly_name__contains="HSSP Sym"))
    print request.user.studentapplication_set.filter(program__pk=72).count()
    
    fields = {}
    for i, timeslot in enumerate(sections_by_slot.keys()): 
        fields['timeslot_'+str(i+1)] = forms.ChoiceField(label="Timeslot "+str(i+1)+" ("+timeslot.pretty_time()+")", choices=[('0',"I'm happy with my current enrollment.")]+[(section.emailcode(), section.emailcode()+": "+section.title()) for section in sections_by_slot[timeslot]])
        fields['orig_timeslot_'+str(i+1)] = forms.ChoiceField(label="Timeslot "+str(i+1)+" ("+timeslot.pretty_time()+")", choices=[('0',"I'm happy with my current enrollment.")]+[(section.emailcode(), section.emailcode()+": "+section.title()) for section in sections_by_slot[timeslot]], widget = forms.HiddenInput, initial="A1234")
    
    context = {}
    context['form'] = type('ClassChangeRequestForm', (forms.Form,), fields)()
    context['timeslots'] = timeslots
    context['enrollments'] = enrollments
    return render_to_response('program/classchangerequest.html', request, (prog, tl), context)


def archives(request, selection, category = None, options = None):
	""" Return a page with class archives """
	
	sortparams = []
	if request.POST and request.POST.has_key('newparam'):
		if request.POST['newparam']:
			sortparams.append(request.POST['newparam'])
		for key in request.POST:
			if key.startswith('sortparam') and request.POST[key] != request.POST['newparam']: sortparams.append(request.POST[key])
	#	The selection variable is the type of data they want to see:
	#	classes, programs, teachers, etc.
	if archive_handlers.has_key(selection):
		return archive_handlers[selection](request, category, options, sortparams)
	
	return render_to_response('users/construction', request, GetNode('Q/Web'), {})

def contact(request, section='esp'):
	"""
	This view should take an email and post to those people.
	"""
	from django.core.mail import send_mail

	if request.GET.has_key('success'):
		return render_to_response('contact_success.html', request, GetNode('Q/Web/about'), {})
	
		
	
	if request.method == 'POST':
		form = ContactForm(request.POST)
		SUBJECT_PREPEND = '[webform]'
                domain = Site.objects.get_current().domain
		
		if form.is_valid():
			
			to_email = []
			usernames = []

			if len(form.cleaned_data['sender'].strip()) == 0:
				email = 'esp@mit.edu'
			else:
				email = form.cleaned_data['sender']
				usernames = ESPUser.objects.filter(email__iexact = email).values_list('username', flat = True)
                
			if form.cleaned_data['cc_myself']:
				to_email.append(email)


			try:
				to_email.append(email_addresses[form.cleaned_data['topic'].lower()])
			except KeyError:
				to_email.append(fallback_address)

			if len(form.cleaned_data['name'].strip()) > 0:
				email = '%s <%s>' % (form.cleaned_data['name'], email)


			t = loader.get_template('email/comment')

			msgtext = t.render(Context({'form': form, 'domain': domain, 'usernames': usernames}))
				
			send_mail(SUBJECT_PREPEND + ' '+ form.cleaned_data['subject'],
				  msgtext,
				  email, to_email, fail_silently = True)

			return HttpResponseRedirect(request.path + '?success')

        
	else:
		initial = {}
		if request.user.is_authenticated():
			initial['sender'] = request.user.email
			initial['name']   = request.user.first_name + ' '+request.user.last_name
		
		if section != '':
			initial['topic'] = section.lower()

		form = ContactForm(initial = initial)
			
	return render_to_response('contact.html', request, GetNode('Q/Web/about'),
						 {'contact_form': form})


def registration_redirect(request):
    """ A view which returns:
        - A redirect to the currently open registration if exactly one registration is open
        - A list of open registration links otherwise
    """
    from esp.users.models import ESPUser, UserBit
    from esp.program.models import Program

    #   Make sure we have an ESPUser
    user = ESPUser(request.user)

    # prepare the rendered page so it points them to open student/teacher reg's
    ctxt = {}
    userrole = {}
    regverb = None
    if user.isStudent():
        userrole['name'] = 'Student'
        userrole['base'] = 'learn'
        userrole['reg'] = 'studentreg'
        regverb = GetNode('V/Deadline/Registration/Student/Classes/OneClass')
    elif user.isTeacher():
        userrole['name'] = 'Teacher'
        userrole['base'] = 'teach'
        userrole['reg'] = 'teacherreg'
        regverb = GetNode('V/Deadline/Registration/Teacher/Classes')
    else:
        #   Default to student registration (this will only show if the program
        #   is found via the 'allowed_student_types' Tag)
        userrole['name'] = user.getUserTypes()[0]
        userrole['base'] = 'learn'
        userrole['reg'] = 'studentreg'
    ctxt['userrole'] = userrole
    ctxt['navnode'] = GetNode('Q/Web/myesp')
    
    if regverb:
        progs_userbit = list(UserBit.find_by_anchor_perms(Program, user=user, verb=regverb))
    else:
        progs_userbit = []
    progs_tag = list(t.target \
            for t in Tag.objects.filter(key = "allowed_student_types").select_related() \
            if isinstance(t.target, Program) \
                and (set(user.getUserTypes()) & set(t.value.split(","))))
    progs = set(progs_userbit + progs_tag)
    print progs
        
    nextreg = UserBit.objects.filter(user__isnull=True, verb=regverb, startdate__gt=datetime.datetime.now()).order_by('startdate')
    progs = list(progs)
    if len(progs) == 1:
        ctxt['prog'] = progs[0]
        ctxt['navnode'] = progs[0].anchor
        return HttpResponseRedirect(u'/%s/%s/%s' % (userrole['base'], progs[0].getUrlBase(), userrole['reg']))
    else:
        if len(progs) > 0:
            ctxt['progs'] = progs
            ctxt['prog'] = progs[0]
        ctxt['nextreg'] = list(nextreg)
        return render_to_response('users/profile_complete.html', request, GetNode('Q/Web'), ctxt)		    
    
@csrf_exempt  ## We want this to work even (especially?) if something's borked with the CSRF cookie logic
def error_reporter(request):
    """ Grab an error submitted as a GET request """
    url = request.GET.get('url', "")
    domain = Site.objects.get_current().domain
    if url[:4] == 'http' and (domain not in (url[7:(7+len(domain))], url[8:(8+len(domain))])):
        ## Punt responses not from us
        return HttpResponse('')  ## Return something, so we don't trigger an error
    
    cookies = StringIO()
    get = StringIO()
    meta = StringIO()
    post = StringIO()

    pprint(dict(request.COOKIES), cookies)
    pprint(dict(request.GET), get)
    pprint(dict(request.META), meta)
    if request.POST:
        pprint(dict(request.POST), post)

    msg = request.GET.get('msg', "(no message)")

    user_str = request.user.username if hasattr(request, 'user') and request.user.is_authenticated() else "(not authenticated)"
    user_agent_str = request.META.get('HTTP_USER_AGENT', "(not specified")

    err_txt = """A user reported an error!

User: %s
Path: %s
UserAgent: %s
GET:
%s
POST:
%s

Cookies:
%s

META:
%s
""" % (user_str, request.path, user_agent_str, get.getvalue(), post.getvalue(), cookies.getvalue(), meta.getvalue())

    mail_admins("[ESP] JS Error: %s" % msg[:100].replace("\n", "").replace("\r", ""), err_txt)

    return HttpResponse('')  ## Return something, so we don't trigger an error
