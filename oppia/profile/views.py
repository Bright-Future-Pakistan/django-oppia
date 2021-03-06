# oppia/profile/views.py
import csv
import datetime
from itertools import chain

from django import forms
import operator
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (authenticate, login)
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Count, Max, Min, Avg, Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext as _
from tastypie.models import ApiKey

from oppia.models import Points, Award, Tracker, Activity
from oppia.permissions import get_user, get_user_courses, can_view_course, can_edit_user
from oppia.profile.forms import LoginForm, RegisterForm, ResetForm, ProfileForm, UploadProfileForm, \
    UserSearchForm
from oppia.profile.models import UserProfile
from oppia.quiz.models import Quiz, QuizAttempt
from oppia.reports.signals import dashboard_accessed
from oppia.summary.models import UserCourseSummary


def filterRedirect(requestContent):
    redirection = requestContent.get('next')
    # Avoid redirecting to logout after login
    if redirection == reverse('profile_logout'):
        return None
    else:
        return redirection

def get_paginated_users(request):
    default_order = 'date_joined'
    ordering = request.GET.get('order_by', None)
    if ordering is None:
        ordering = default_order

    users = User.objects.all().order_by(ordering).select_related('api_key__key')
    paginator = Paginator(users, 5)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    return ordering, paginator.page(page)

def login_view(request):
    username = password = ''
    
    # if already logged in
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('oppia_home'))
    
    if request.POST:
        form = LoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        next = filterRedirect(request.POST)

        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request,user)
            if next is not None:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse('oppia_home'))
    else:
        form = LoginForm(initial={'next':filterRedirect(request.GET),})
        
    return render_to_response('oppia/form.html',
                              {'username': username, 
                               'form': form, 
                               'title': _(u'Login')},
                              context_instance=RequestContext(request),)

def register(request):
    if not settings.OPPIA_ALLOW_SELF_REGISTRATION:
        raise Http404
    
    if request.method == 'POST': # if form submitted...
        form = RegisterForm(request.POST)
        if form.is_valid(): # All validation rules pass
            # Create new user
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            user = User.objects.create_user(username, email, password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user_profile = UserProfile()
            user_profile.user = user
            user_profile.job_title = form.cleaned_data.get("job_title")
            user_profile.organisation = form.cleaned_data.get("organisation")
            user_profile.save()
            u = authenticate(username=username, password=password)
            if u is not None:
                if u.is_active:
                    login(request, u)
                    return HttpResponseRedirect('thanks/')
            return HttpResponseRedirect('thanks/') # Redirect after POST
    else:
        form = RegisterForm(initial={'next':filterRedirect(request.GET),})

    return render_to_response('oppia/form.html',
                              {'form': form,
                               'title': _(u'Register'), },
                               context_instance=RequestContext(request),)

def reset(request):
    if request.method == 'POST': # if form submitted...
        form = ResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            try:
                user = User.objects.get(username__exact=username)
            except User.DoesNotExist:
                user = User.objects.get(email__exact=username)
            newpass = User.objects.make_random_password(length=8)
            user.set_password(newpass)
            user.save()
            if request.is_secure():
                prefix = 'https://'
            else:
                prefix = 'http://'
            # TODO - better way to manage email message content
            send_mail('BrightFuture: Password reset', 'Here is your new password for BrightFuture: '+newpass
                      + '\n\nWhen you next log in you can update your password to something more memorable.'
                      + '\n\n' + prefix + request.META['SERVER_NAME'] ,
                      settings.SERVER_EMAIL, [user.email], fail_silently=False)
            return HttpResponseRedirect('sent')
    else:
        form = ResetForm() # An unbound form

    return render_to_response(
                  'oppia/form.html',
                  {'form': form,
                   'title': _(u'Reset password')},
                  context_instance=RequestContext(request))

def edit(request, user_id=0):
    if user_id != 0:
        if can_edit_user(request, user_id):
            view_user = User.objects.get(pk=user_id)
        else:
            return HttpResponse('Unauthorized', status=401)
    else:
        view_user = request.user

    key = ApiKey.objects.get(user = view_user)
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            # update basic data
            email = form.cleaned_data.get("email")
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            view_user.email = email
            view_user.first_name = first_name
            view_user.last_name = last_name
            view_user.save()

            try:
                user_profile = UserProfile.objects.get(user=view_user)
                user_profile.job_title = form.cleaned_data.get("job_title")
                user_profile.organisation = form.cleaned_data.get("organisation")
                user_profile.save()
            except UserProfile.DoesNotExist:
                user_profile = UserProfile()
                user_profile.user = view_user
                user_profile.job_title = form.cleaned_data.get("job_title")
                user_profile.organisation = form.cleaned_data.get("organisation")
                user_profile.save()
            messages.success(request, _(u"Profile updated"))

            # if password should be changed
            password = form.cleaned_data.get("password")
            if password:
                view_user.set_password(password)
                view_user.save()
                messages.success(request, _(u"Password updated"))
    else:
        try:
            user_profile = UserProfile.objects.get(user=view_user)
        except UserProfile.DoesNotExist:
            user_profile = UserProfile()
        form = ProfileForm(initial={'username':view_user.username,
                                    'email':view_user.email,
                                    'first_name':view_user.first_name,
                                    'last_name':view_user.last_name,
                                    'api_key': key.key,
                                    'job_title': user_profile.job_title,
                                    'organisation': user_profile.organisation,})

    return render_to_response(
                  'oppia/profile/profile.html',
                  {'form': form,},
                  context_instance=RequestContext(request))

def points(request):
    points = Points.objects.filter(user=request.user).order_by('-date')
    paginator = Paginator(points, 25) # Show 25 contacts per page

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        mypoints = paginator.page(page)
    except (EmptyPage, InvalidPage):
        mypoints = paginator.page(paginator.num_pages)
    return render_to_response('oppia/profile/points.html',
                              {'page': mypoints,},
                              context_instance=RequestContext(request),)

def badges(request):
    awards = Award.objects.filter(user=request.user).order_by('-award_date')
    return render_to_response('oppia/profile/badges.html',
                              {'awards': awards,},
                              context_instance=RequestContext(request),)


def user_activity(request, user_id):

    view_user, response = get_user(request, user_id)
    if response is not None:
        return response

    dashboard_accessed.send(sender=None, request=request, data=None)

    cohort_courses, other_courses, all_courses = get_user_courses(request, view_user)

    courses = []
    for course in all_courses:
        course_stats = UserCourseSummary.objects.filter(user=view_user, course=course)[0]
        data = {'course': course,
                'no_quizzes_completed': course_stats.quizzes_passed ,
                'pretest_score': course_stats.pretest_score,
                'no_activities_completed': course_stats.completed_activities,
                'no_media_viewed': course_stats.media_viewed,
                'no_points': course_stats.points,
                'no_badges': course_stats.badges_achieved,}
        courses.append(data)

    order_options = ['course', 'no_quizzes_completed', 'pretest_score',
                     'no_activities_completed','no_points', 'no_badges', 'no_media_viewed']
    default_order = 'course'

    ordering = request.GET.get('order_by', default_order)
    inverse_order = ordering.startswith('-')
    if inverse_order:
        ordering = ordering[1:]

    if ordering not in order_options:
        ordering = default_order
        inverse_order = False

    courses.sort(key=operator.itemgetter(ordering), reverse=inverse_order)

    activity = []
    start_date = timezone.now() - datetime.timedelta(days=31)
    end_date = timezone.now()
    no_days = (end_date-start_date).days + 1

    course_ids = list(chain(cohort_courses.values_list('id',flat=True),other_courses.values_list('id',flat=True)))
    trackers = Tracker.objects.filter(course__id__in=course_ids,
                                      user=view_user,
                                      tracker_date__gte=start_date,
                                      tracker_date__lte=end_date) \
                                      .extra({'activity_date':"date(tracker_date)"}) \
                                      .values('activity_date') \
                                      .annotate(count=Count('id'))
    for i in range(0,no_days,+1):
        temp = start_date + datetime.timedelta(days=i)
        count = next((dct['count'] for dct in trackers if dct['activity_date'] == temp.date()), 0)
        activity.append([temp.strftime("%d %b %Y"),count])

    return render_to_response('oppia/profile/user-scorecard.html',
                              {'view_user': view_user,
                               'courses': courses,
                               'page_ordering': ('-' if inverse_order else '') + ordering,
                               'activity_graph_data': activity },
                              context_instance=RequestContext(request))

def user_course_activity_view(request, user_id, course_id):

    view_user, response = get_user(request, user_id)
    if response is not None:
        return response

    dashboard_accessed.send(sender=None, request=request, data=None)
    course = can_view_course(request, course_id)

    act_quizzes = Activity.objects.filter(section__course=course,type=Activity.QUIZ).order_by('section__order','order')

    quizzes_attempted = 0
    quizzes_passed = 0
    course_pretest = None

    quizzes = []
    for aq in act_quizzes:
        try:
            quiz = Quiz.objects.get(quizprops__value=aq.digest, quizprops__name="digest")
        except Quiz.DoesNotExist:
            quiz = None


        attempts = QuizAttempt.objects.filter(quiz=quiz, user=view_user)
        num_attempts = attempts.count()
        passed = False
        if num_attempts > 0:

            quiz_maxscore = float(attempts[0].maxscore)
            attemps_stats = attempts.aggregate(max=Max('score'), min=Min('score'), avg=Avg('score'))
            max_score = 100*float(attemps_stats['max']) / quiz_maxscore
            min_score = 100*float(attemps_stats['min']) / quiz_maxscore
            avg_score = 100*float(attemps_stats['avg']) / quiz_maxscore
            first_date = attempts.aggregate(date=Min('attempt_date'))['date']
            recent_date = attempts.aggregate(date=Max('attempt_date'))['date']
            first_score = 100*float(attempts.filter(attempt_date = first_date)[0].score) / quiz_maxscore
            latest_score = 100*float(attempts.filter(attempt_date = recent_date)[0].score) / quiz_maxscore

            passed = max_score is not None and max_score > 75
            if aq.section.order == 0:
                course_pretest = first_score
            else:
                quizzes_attempted += 1
                quizzes_passed = (quizzes_passed + 1) if passed else quizzes_passed

        else:
            max_score = None
            min_score = None
            avg_score = None
            first_score = None
            latest_score = None

        quiz = {'quiz': aq,
                'quiz_order': aq.order,
                'no_attempts': num_attempts,
                'max_score': max_score,
                'min_score': min_score,
                'first_score': first_score,
                'latest_score': latest_score,
                'avg_score': avg_score,
                'passed': passed
                 }
        quizzes.append(quiz)

    activities_completed = course.get_activities_completed(course,view_user)
    activities_total = course.get_no_activities()
    activities_percent = (activities_completed * 100) / activities_total

    activity = []
    start_date = timezone.now() - datetime.timedelta(days=31)
    end_date = timezone.now()
    no_days = (end_date-start_date).days + 1

    trackers = Tracker.objects.filter(course=course,
                                      user=view_user,
                                      tracker_date__gte=start_date,
                                      tracker_date__lte=end_date) \
                                      .extra({'activity_date':"date(tracker_date)"}) \
                                      .values('activity_date') \
                                      .annotate(count=Count('id'))
    for i in range(0,no_days,+1):
        temp = start_date + datetime.timedelta(days=i)
        count = next((dct['count'] for dct in trackers if dct['activity_date'] == temp.date()), 0)
        activity.append([temp.strftime("%d %b %Y"),count])

    order_options = ['quiz_order', 'no_attempts', 'max_score', 'min_score',
                     'first_score', 'latest_score', 'avg_score']
    default_order = 'quiz_order'
    ordering = request.GET.get('order_by', default_order)
    inverse_order = ordering.startswith('-')
    if inverse_order:
        ordering = ordering[1:]
    if ordering not in order_options:
        ordering = default_order
        inverse_order = False

    quizzes.sort(key=operator.itemgetter(ordering), reverse=inverse_order)

    return render_to_response('oppia/profile/user-course-scorecard.html',
                              {'view_user': view_user,
                               'course': course,
                               'quizzes': quizzes,
                               'quizzes_passed':quizzes_passed,
                               'quizzes_attempted':quizzes_attempted,
                               'pretest_score': course_pretest,
                               'activities_completed': activities_completed,
                               'activities_total': activities_total,
                               'activities_percent': activities_percent,
                               'page_ordering': ('-' if inverse_order else '') + ordering,
                               'activity_graph_data': activity },
                              context_instance=RequestContext(request))

def upload_view(request):
    if not request.user.is_staff:
        raise Http404

    if request.method == 'POST': # if form submitted...
        form = UploadProfileForm(request.POST,request.FILES)
        if form.is_valid():
            request.FILES['upload_file'].open("rb")
            csv_file = csv.DictReader(request.FILES['upload_file'].file)
            required_fields = ['username','firstname','lastname','email']
            results = []
            try:
                for row in csv_file:
                    # check all required fields defined
                    all_defined = True
                    for rf in required_fields:
                        if rf not in row or row[rf].strip() == '':
                            result = {}
                            result['username'] = row['username']
                            result['created'] = False
                            result['message'] = _(u'No %s set' % rf)
                            results.append(result)
                            all_defined = False

                    if not all_defined:
                        continue

                    user = User()
                    user.username = row['username']
                    user.first_name = row['firstname']
                    user.last_name = row['lastname']
                    user.email = row['email']
                    auto_password = False
                    if 'password' in row:
                        user.set_password(row['password'])
                    else:
                        password = User.objects.make_random_password()
                        user.set_password(password)
                        auto_password = True
                    try:
                        user.save()
                        up = UserProfile()
                        up.user = user
                        for col_name in row:
                            setattr(up, col_name, row[col_name])
                        up.save()
                        result = {}
                        result['username'] = row['username']
                        result['created'] = True
                        if auto_password:
                            result['message'] = _(u'User created with password: %s' % password)
                        else:
                            result['message'] = _(u'User created')
                        results.append(result)
                    except IntegrityError as ie:
                        result = {}
                        result['username'] = row['username']
                        result['created'] = False
                        result['message'] = _(u'User already exists')
                        results.append(result)
                        continue
            except:
                result = {}
                result['username'] = None
                result['created'] = False
                result['message'] = _(u'Could not parse file')
                results.append(result)

    else:
        results = []
        form = UploadProfileForm()

    return render_to_response('oppia/profile/upload.html',
                              {'form': form,
                               'results': results},
                              context_instance=RequestContext(request),)

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.

    '''
    query = None # Query to search in every field
    for field_name in search_fields:
        q = Q(**{"%s__icontains" % field_name: query_string})
        query = q if query is None else (query | q)

    return query

def search_users(request):

    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)

    users = User.objects

    filtered = False
    search_form = UserSearchForm(request.GET,request.FILES)
    if search_form.is_valid():
        filters = {}
        for row in search_form.cleaned_data:
            if search_form.cleaned_data[row]:
                if row is 'register_start_date':
                    filters['date_joined__gte'] = search_form.cleaned_data[row]
                elif row is 'register_end_date':
                    filters['date_joined__lte'] = search_form.cleaned_data[row]
                elif isinstance(search_form.fields[row], forms.CharField):
                    filters["%s__icontains" % row] = search_form.cleaned_data[row]
                else:
                    filters[row] = search_form.cleaned_data[row]
        if filters:
            print filters
            users = users.filter(**filters)
            filtered = True

    if not filtered:
        users = users.all()

    query_string = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        filter_query = get_query(query_string, ['username','first_name', 'last_name','email',])
        users = users.filter(filter_query)

    ordering = request.GET.get('order_by', None)
    if ordering is None:
        ordering = 'first_name'

    users = users.order_by(ordering)
    paginator = Paginator(users, 10) # Show 25 per page

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        users = paginator.page(page)
    except (EmptyPage, InvalidPage):
        users = paginator.page(paginator.num_pages)

    return render_to_response('oppia/profile/search_user.html',
                              {
                                'quicksearch':query_string,
                                'search_form':search_form,
                                'advanced_search':filtered,
                                'page': users,
                                'page_ordering':ordering
                              },
                              context_instance=RequestContext(request),)

def export_users(request):

    if not request.user.is_staff:
        raise Http404

    ordering, users = get_paginated_users(request)
    for user in users:
        try:
            user.apiKey = user.api_key.key
        except ApiKey.DoesNotExist:
            #if the user doesn't have an apiKey yet, generate it
            user.apiKey = ApiKey.objects.create(user=user).key

    template = 'export-users.html'
    if request.is_ajax():
        template = 'users-paginated-list.html'

    return render_to_response('oppia/profile/' + template,
                              {
                                  'page': users,
                                  'page_ordering':ordering,
                                  'users_list_template':'export'
                              },
                              context_instance=RequestContext(request),)

def list_users(request):
    ordering, users = get_paginated_users(request)
    return render_to_response('oppia/profile/users-paginated-list.html',
                              {
                                  'page': users,
                                  'page_ordering':ordering,
                                  'users_list_template':'select',
                                  'ajax_url':request.path
                              },
                              context_instance=RequestContext(request),)
