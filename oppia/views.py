# oppia/views.py
import datetime
import json
from wsgiref.util import FileWrapper

import operator
import os
import tablib
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from oppia.forms import ActivityScheduleForm, CohortForm
from oppia.forms import UploadCourseStep1Form, UploadCourseStep2Form, ScheduleForm, DateRangeForm, DateRangeIntervalForm
from oppia.models import ActivitySchedule, Activity, Points
from oppia.models import Tracker, Tag, CourseTag, Schedule, CourseCohort
from oppia.permissions import *
from oppia.profile.models import UserProfile
from oppia.profile.views import get_paginated_users
from oppia.quiz.models import Quiz, QuizAttempt, QuizAttemptResponse
from oppia.reports.signals import dashboard_accessed
from oppia.summary.models import UserCourseSummary, CourseDailyStats
from uploader import handle_uploaded_file


def server_view(request):
    return render_to_response('oppia/server.html',  
                              {'settings': settings}, 
                              content_type="application/json", 
                              context_instance=RequestContext(request))

def about_view(request):
    return render_to_response('oppia/about.html',  
                              {'settings': settings}, 
                              context_instance=RequestContext(request))
    
def home_view(request):

    activity = []
    leaderboard = None

    if request.user.is_authenticated():
        # create profile if none exists (historical for very old users)
        try:
            up = request.user.userprofile
        except UserProfile.DoesNotExist:
            up = UserProfile()
            up.user= request.user
            up.save()
        
        dashboard_accessed.send(sender=None, request=request, data=None)
        
        # if user is student redirect to their scorecard
        if up.is_student_only():
            return HttpResponseRedirect(reverse('profile_user_activity', args=[request.user.id]))
        
        # is user is teacher redirect to teacher home
        if up.is_teacher_only():
            return HttpResponseRedirect(reverse('oppia_teacher_home'))
        
        start_date = timezone.now() - datetime.timedelta(days=31)
        end_date = timezone.now()
        interval = 'days'
        if request.method == 'POST':
            form = DateRangeIntervalForm(request.POST)
            if form.is_valid():
                start_date = form.cleaned_data.get("start_date")  
                start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d")
                end_date = form.cleaned_data.get("end_date")
                end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d")   
                interval =  form.cleaned_data.get("interval")          
        else:
            data = {}
            data['start_date'] = start_date
            data['end_date'] = end_date
            data['interval'] = interval
            form = DateRangeIntervalForm(initial=data)
        
        if interval == 'days':
            no_days = (end_date-start_date).days + 1
            tracker_stats = CourseDailyStats.objects.filter(day__gte=start_date, day__lte=end_date).values('day').annotate(count=Sum('total'))

            for i in range(0,no_days,+1):
                temp = start_date + datetime.timedelta(days=i)
                count = next((dct['count'] for dct in tracker_stats if dct['day'] == temp.date()), 0)
                activity.append([temp.strftime("%d %b %Y"),count])
        else:
            delta = relativedelta(months=+1)
            
            no_months = 0
            tmp_date = start_date
            while tmp_date <= end_date:
                print tmp_date
                tmp_date += delta
                no_months += 1
                
            for i in range(0,no_months,+1):
                temp = start_date + relativedelta(months=+i)
                month = temp.strftime("%m")
                year = temp.strftime("%Y")
                count = CourseDailyStats.objects.filter(day__month=month, day__year=year).aggregate(total=Sum('total')).get('total',0)
                activity.append([temp.strftime("%b %Y"), 0 if count is None else count])

            print activity

        leaderboard = Points.get_leaderboard(10)

    else:
        form = None

    return render_to_response('oppia/home.html',
                              {'form': form,
                               'activity_graph_data': activity, 
                               'leaderboard': leaderboard}, 
                              context_instance=RequestContext(request))

def teacher_home_view(request):
    cohorts, response = get_cohorts(request)
    if response is not None:
        return response
    
    start_date = timezone.now() - datetime.timedelta(days=31)
    end_date = timezone.now()
        
    # get student activity
    activity = []
    no_days = (end_date-start_date).days + 1
    students =  User.objects.filter(participant__role=Participant.STUDENT, participant__cohort__in=cohorts).distinct()   
    courses = Course.objects.filter(coursecohort__cohort__in=cohorts).distinct()
    trackers = Tracker.objects.filter(course__in=courses, 
                                       user__in=students,  
                                       tracker_date__gte=start_date,
                                       tracker_date__lte=end_date).extra({'activity_date':"date(tracker_date)"}).values('activity_date').annotate(count=Count('id'))
    for i in range(0,no_days,+1):
        temp = start_date + datetime.timedelta(days=i)
        count = next((dct['count'] for dct in trackers if dct['activity_date'] == temp.date()), 0)
        activity.append([temp.strftime("%d %b %Y"),count])
    
    return render_to_response('oppia/home-teacher.html',
                              {'cohorts': cohorts,
                               'activity_graph_data': activity, }, 
                              context_instance=RequestContext(request))

def render_courses_list(request, courses, params=None):

    if params is None:
        params = {}

    course_filter = request.GET.get('visibility', '')
    if course_filter == 'draft':
        courses = courses.filter(is_draft=True)
    elif course_filter == 'archived':
        courses = courses.filter(is_archived=True)

    tag_list = Tag.objects.all().exclude(coursetag=None).order_by('name')
    paginator = Paginator(courses, 25) # Show 25 per page
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET. get('page', '1'))
    except ValueError:
        page = 1

    course_stats = list (UserCourseSummary.objects.filter(course__in=courses).values('course').annotate(distinct=Count('user'), total=Sum('total_downloads') ))

    try:
        courses = paginator.page(page)
    except (EmptyPage, InvalidPage):
        courses = paginator.page(paginator.num_pages)


    for course in courses:
        access_detail, response = can_view_course_detail(request,course.id)
        course.can_edit = can_edit_course(request,course.id)
        course.access_detail = access_detail is not None

        for stats in course_stats:
            if stats['course'] == course.id:
                course.distinct_downloads = stats['distinct']
                course.total_downloads = stats['total']
                course_stats.remove(stats) #remove the element to optimize next searchs
                continue

    params['page'] = courses
    params['tag_list'] = tag_list
    params['course_filter'] = course_filter

    return render_to_response('oppia/course/courses-list.html', params,
                          context_instance=RequestContext(request))


def courses_list_view(request):

    if request.is_ajax():
        #if we are requesting via ajax, just show the course list
        ordering, courses = get_paginated_courses(request)
        return render_to_response('oppia/course/courses-paginated-list.html',
                              {
                                  'page': courses,
                                  'page_ordering':ordering,
                                  'ajax_url':request.path
                              },
                              context_instance=RequestContext(request),)
    else:
        courses, response = can_view_courses_list(request)
        if response is not None:
            return response

        dashboard_accessed.send(sender=None, request=request, data=None)
        return render_courses_list(request, courses)


def course_download_view(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise Http404()
    file_to_download = course.getAbsPath();
    wrapper = FileWrapper(file(file_to_download))
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Length'] = os.path.getsize(file_to_download)
    response['Content-Disposition'] = 'attachment; filename="%s"' %(course.filename)
    return response

def tag_courses_view(request, tag_id):
    courses, response = can_view_courses_list(request)
    if response is not None:
        return response
    courses = courses.filter(coursetag__tag__pk=tag_id)

    dashboard_accessed.send(sender=None, request=request, data=None)
    return render_courses_list(request, courses, {'current_tag': tag_id})

        
def upload_step1(request):
    if not request.user.userprofile.get_can_upload():
        return HttpResponse('Unauthorized', status=401)
        
    if request.method == 'POST':
        form = UploadCourseStep1Form(request.POST,request.FILES)
        if form.is_valid(): # All validation rules pass
            extract_path = os.path.join(settings.COURSE_UPLOAD_DIR, 'temp', str(request.user.id))
            course = handle_uploaded_file(request.FILES['course_file'], extract_path, request, request.user)
            if course:
                return HttpResponseRedirect(reverse('oppia_upload2', args=[course.id])) # Redirect after POST
            else:
                os.remove(settings.COURSE_UPLOAD_DIR + request.FILES['course_file'].name)
    else:
        form = UploadCourseStep1Form() # An unbound form

    return render_to_response('oppia/upload.html', 
                              {'form': form,
                               'title':_(u'Upload Course - step 1')},
                              context_instance=RequestContext(request))

def upload_step2(request, course_id, editing=False):

    if editing and not can_edit_course(request, course_id):
        return HttpResponse('Unauthorized', status=401)
    elif not request.user.userprofile.get_can_upload():
        return HttpResponse('Unauthorized', status=401)
        
    course = Course.objects.get(pk=course_id)
    
    if request.method == 'POST':
        form = UploadCourseStep2Form(request.POST,request.FILES)
        if form.is_valid(): # All validation rules pass
            is_draft = form.cleaned_data.get("is_draft")
            if course:
                #add the tags
                tags = form.cleaned_data.get("tags").strip().split(",")
                is_draft = form.cleaned_data.get("is_draft")
                if len(tags) > 0:
                    course.is_draft = is_draft
                    course.save()
                    for t in tags:
                        try: 
                            tag = Tag.objects.get(name__iexact=t.strip())
                        except Tag.DoesNotExist:
                            tag = Tag()
                            tag.name = t.strip()
                            tag.created_by = request.user
                            tag.save()
                        # add tag to course
                        try:
                            ct = CourseTag.objects.get(course=course,tag=tag)
                        except CourseTag.DoesNotExist:
                            ct = CourseTag()
                            ct.course = course
                            ct.tag = tag
                            ct.save()

                redirect = 'oppia_course' if editing else 'oppia_upload_success'
                return HttpResponseRedirect(reverse(redirect)) # Redirect after POST
    else:
        form = UploadCourseStep2Form(initial={'tags':course.get_tags(),
                                    'is_draft':course.is_draft,}) # An unbound form

    page_title = _(u'Upload Course - step 2') if not editing else _(u'Edit course')
    return render_to_response('oppia/upload.html', 
                              {'form': form,
                               'course_title':course.title,
                               'editing':editing,
                               'title':page_title},
                              context_instance=RequestContext(request))

def generate_graph_data(dates_types_stats, is_monthly=False):
    dates = []

    current_date = None
    current_stats = {}

    for date in dates_types_stats:
        if is_monthly:
            #depending if it is monthly or daily, we parse differently the day "tag"
            day = datetime.date(month=date['month'], year=date['year'], day=1).strftime("%b %y")
        else:
            day = date['day'].strftime("%d %b %y")

        if current_date is None or day != current_date:
            if current_date != None:
                dates.append([current_date, current_stats])
            current_date = day  
            current_stats = {'page':0, 'quiz':0, 'media':0, 'resource':0, 'monitor': 0, 'total':0}

        current_stats[date['type']] = date['total']
        current_stats['total'] += date['total']

    if current_date is not None:
        dates.append([current_date, current_stats])

    return dates


def recent_activity(request,course_id):

    course, response = can_view_course_detail(request, course_id)

    if response is not None:
        return response

    dashboard_accessed.send(sender=None, request=request, data=course)

    start_date = datetime.datetime.now() - datetime.timedelta(days=31)
    end_date = datetime.datetime.now()
    interval = 'days'

    if request.method == 'POST':
        form = DateRangeIntervalForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get("start_date")
            start_date = datetime.datetime.strptime(start_date + " 00:00:00","%Y-%m-%d %H:%M:%S")
            end_date = form.cleaned_data.get("end_date")
            end_date = datetime.datetime.strptime(end_date + " 23:59:59","%Y-%m-%d %H:%M:%S")
            interval =  form.cleaned_data.get("interval")
    else:
        data = {}
        data['start_date'] = start_date
        data['end_date'] = end_date
        data['interval'] = interval
        form = DateRangeIntervalForm(initial=data)

    dates = []
    if interval == 'days':
        daily_stats = CourseDailyStats.objects.filter(course=course, day__gte=start_date, day__lte=end_date)\
                        .values('day','type')\
                        .annotate(total=Sum('total'))
    
        dates = generate_graph_data(daily_stats, False)

    else:
        monthly_stats = CourseDailyStats.objects.filter(course=course, day__gte=start_date, day__lte=end_date)\
                        .extra({'month':'month(day)', 'year':'year(day)'})\
                        .values('month','year','type')\
                        .annotate(total=Sum('total'))\
                        .order_by('year','month')

        dates = generate_graph_data(monthly_stats, True)

    leaderboard = Points.get_leaderboard(10, course)
    return render_to_response('oppia/course/activity.html',
                              {'course': course,
                               'form': form,
                                'data':dates, 
                                'leaderboard':leaderboard}, 
                              context_instance=RequestContext(request))

def recent_activity_detail(request,course_id):
    course, response = can_view_course_detail(request, course_id)
    
    if response is not None:
        return response
        
    start_date = datetime.datetime.now() - datetime.timedelta(days=31)
    end_date = datetime.datetime.now()
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get("start_date")  
            start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d")
            end_date = form.cleaned_data.get("end_date")
            end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d") 
            trackers = Tracker.objects.filter(course=course,tracker_date__gte=start_date, tracker_date__lte=end_date).order_by('-tracker_date')
        else:
            trackers = Tracker.objects.filter(course=course).order_by('-tracker_date')             
    else:
        data = {}
        data['start_date'] = start_date
        data['end_date'] = end_date
        form = DateRangeForm(initial=data)
        trackers = Tracker.objects.filter(course=course).order_by('-tracker_date')
        
    paginator = Paginator(trackers, 25)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        tracks = paginator.page(page)
        for t in tracks:  
            t.data_obj = []
            try:
                data_dict = json.loads(t.data)
                for key, value in data_dict.items():
                    t.data_obj.append([key,value])
            except ValueError:
                pass
            t.data_obj.append(['agent',t.agent])
            t.data_obj.append(['ip',t.ip])
    except (EmptyPage, InvalidPage):
        tracks = paginator.page(paginator.num_pages)
    
    return render_to_response('oppia/course/activity-detail.html',
                              {'course': course,
                               'form': form, 
                               'page':tracks,}, 
                              context_instance=RequestContext(request))


def export_tracker_detail(request,course_id):
    course, response = can_view_course_detail(request, course_id)
    
    if response is not None:
        return response
    
    headers = ('Date', 'UserId', 'Type', 'Activity Title', 'Section Title', 'Time Taken', 'IP Address', 'User Agent', 'Language')
    data = []
    data = tablib.Dataset(*data, headers=headers)
    trackers = Tracker.objects.filter(course=course).order_by('-tracker_date')
    for t in trackers:
        try:
            data_dict = json.loads(t.data)
            if 'lang' in data_dict:
                lang = data_dict['lang']
            else:
                lang = ""
            data.append((t.tracker_date.strftime('%Y-%m-%d %H:%M:%S'), t.user.id, t.type, t.get_activity_title(), t.get_section_title(), t.time_taken, t.ip, t.agent, lang))
        except ValueError:
            data.append((t.tracker_date.strftime('%Y-%m-%d %H:%M:%S'), t.user.id, t.type, "", "", t.time_taken, t.ip, t.agent, ""))
            
    response = HttpResponse(data.xls, content_type='application/vnd.ms-excel;charset=utf-8')
    response['Content-Disposition'] = "attachment; filename=export.xls"

    return response
    
def schedule(request,course_id):
    course = check_owner(request,course_id)    
    schedules = Schedule.objects.filter(course=course)
    return render_to_response('oppia/course/schedules.html',{'course': course,'schedules':schedules,}, context_instance=RequestContext(request))
    
def schedule_add(request,course_id):
    course = check_owner(request,course_id)
    ActivityScheduleFormSet = formset_factory(ActivityScheduleForm, extra=0)

    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        formset = ActivityScheduleFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            schedule = Schedule()
            schedule.course = course
            schedule.title = form.cleaned_data.get("title").strip()
            schedule.default = form.cleaned_data.get("default")
            schedule.created_by = request.user
            
            # remvoe any existing default for this schedule
            if schedule.default:
                Schedule.objects.filter(course=course).update(default=False)
                
            schedule.save()
            
            for f in formset:
                act_sched = ActivitySchedule()
                start_date = f.cleaned_data.get("start_date")
                end_date = f.cleaned_data.get("end_date")
                digest = f.cleaned_data.get("digest")
                if start_date is not None:
                    act_sched = ActivitySchedule()
                    act_sched.schedule = schedule
                    act_sched.start_date = start_date
                    act_sched.end_date = end_date
                    act_sched.digest = digest.strip()
                    act_sched.save()
            return HttpResponseRedirect('../saved/')
    else:
        activities = Activity.objects.filter(section__course= course)
        initial = []
        section = None
        start_date = datetime.datetime.now() 
        end_date = datetime.datetime.now() + datetime.timedelta(days=7)
        for a in activities:
            if a.section != section:
                section = a.section
                start_date = start_date + datetime.timedelta(days=7)
                end_date = end_date + datetime.timedelta(days=7)
            data = {}
            data['title'] = a.title
            data['digest'] = a.digest
            data['section'] = a.section.title
            data['start_date'] = start_date
            data['end_date'] = end_date
            initial.append(data)
            form = ScheduleForm()
        formset = ActivityScheduleFormSet(initial=initial)

    return render(request, 'oppia/schedule-form.html', {'form': form, 'formset': formset,'course':course, })

def schedule_edit(request,course_id, schedule_id):
    course = check_owner(request,course_id)
    schedule = Schedule.objects.get(pk=schedule_id)
    ActivityScheduleFormSet = formset_factory(ActivityScheduleForm, extra=0)
    activities = Activity.objects.filter(section__course = course)
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        formset = ActivityScheduleFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            schedule.title = form.cleaned_data.get("title").strip()
            schedule.default = form.cleaned_data.get("default")
            schedule.lastupdated_date = datetime.datetime.now()
            
            # remove any existing default for this schedule
            if schedule.default:
                Schedule.objects.filter(course=course).update(default=False)
                
            schedule.save()
            
            # remove all the old schedule Activities
            ActivitySchedule.objects.filter(schedule=schedule).delete()
            
            for f in formset:
                act_sched = ActivitySchedule()
                start_date = f.cleaned_data.get("start_date")
                end_date = f.cleaned_data.get("end_date")
                digest = f.cleaned_data.get("digest")
                if start_date is not None:
                    act_sched = ActivitySchedule()
                    act_sched.schedule = schedule
                    act_sched.start_date = start_date
                    act_sched.end_date = end_date
                    act_sched.digest = digest.strip()
                    act_sched.save()
            return HttpResponseRedirect('../saved/')
    else:
        initial = []
        section = None
        for a in activities:
            if a.section != section:
                section = a.section
            data = {}
            data['title'] = a.title
            data['digest'] = a.digest
            data['section'] = a.section.title
            try:
                act_s = ActivitySchedule.objects.get(schedule=schedule,digest = a.digest)
                start_date = act_s.start_date
                end_date = act_s.end_date
            except ActivitySchedule.DoesNotExist:
                start_date = None
                end_date = None
            data['start_date'] = start_date
            data['end_date'] = end_date
            initial.append(data)
        form = ScheduleForm(initial={'title':schedule.title,
                                    'default':schedule.default})
        formset = ActivityScheduleFormSet(initial=initial)

    return render(request, 'oppia/schedule-form.html', {'form': form, 'formset': formset,'course':course, })

def schedule_saved(request, course_id, schedule_id=None):
    course = check_owner(request,course_id)
    return render_to_response('oppia/schedule-saved.html', 
                              {'course': course},
                              context_instance=RequestContext(request))
 
def cohort_list_view(request):
    if not request.user.is_staff:
        raise Http404  
    cohorts = Cohort.objects.all()
    return render_to_response('oppia/course/cohorts-list.html',
                              {'cohorts':cohorts,}, 
                              context_instance=RequestContext(request))


def get_paginated_courses(request):
    default_order = 'lastupdated_date'
    ordering = request.GET.get('order_by', None)
    if ordering is None:
        ordering = default_order

    courses = Course.objects.all().order_by(ordering)
    paginator = Paginator(courses, 5)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    return ordering, paginator.page(page)

def cohort_add(request):
    if not can_add_cohort(request):
        return HttpResponse('Unauthorized', status=401)   
    
    if request.method == 'POST':
        form = CohortForm(request.POST.copy())
        if form.is_valid(): # All validation rules pass
            cohort = Cohort()
            cohort.start_date = form.cleaned_data.get("start_date")
            cohort.end_date = form.cleaned_data.get("end_date")
            cohort.description = form.cleaned_data.get("description").strip()
            cohort.save()
            
            students = form.cleaned_data.get("students").strip().split(",")
            if len(students) > 0:
                for s in students:
                    try:
                        student = User.objects.get(username=s.strip())
                        participant = Participant()
                        participant.cohort = cohort
                        participant.user = student
                        participant.role = Participant.STUDENT
                        participant.save()
                    except User.DoesNotExist:
                        pass
                    
            teachers = form.cleaned_data.get("teachers").strip().split(",")
            if len(teachers) > 0:
                for t in teachers:
                    try:
                        teacher = User.objects.get(username=t.strip())
                        participant = Participant()
                        participant.cohort = cohort
                        participant.user = teacher
                        participant.role = Participant.TEACHER
                        participant.save()
                    except User.DoesNotExist:
                        pass
             
            courses = form.cleaned_data.get("courses").strip().split(",")
            if len(courses) > 0:
                for c in courses:
                    try:
                        course = Course.objects.get(shortname=c.strip())
                        CourseCohort(cohort=cohort, course=course).save()
                    except Course.DoesNotExist:
                        pass
                           
            return HttpResponseRedirect('../') # Redirect after POST
        else:
            #If form is not valid, clean the groups data
            form.data['teachers'] = None
            form.data['courses'] = None
            form.data['students'] = None
           
    else:
        form = CohortForm() # An unbound form

    ordering, users = get_paginated_users(request)
    c_ordering, courses = get_paginated_courses(request)

    return render(request, 'oppia/cohort-form.html',{
                                'form': form,
                                'page': users,
                                'courses_page': courses,
                                'courses_ordering': c_ordering,
                                'page_ordering':ordering,
                                'users_list_template':'select'
                             },context_instance=RequestContext(request))

def cohort_view(request,cohort_id):
    cohort, response = can_view_cohort(request,cohort_id)
    
    if response is not None:
        return response
    
    start_date = timezone.now() - datetime.timedelta(days=31)
    end_date = timezone.now()
        
    # get student activity
    student_activity = []
    no_days = (end_date-start_date).days + 1
    students =  User.objects.filter(participant__role=Participant.STUDENT, participant__cohort=cohort)    
    trackers = Tracker.objects.filter(course__coursecohort__cohort=cohort, 
                                       user__is_staff=False,
                                       user__in=students,  
                                       tracker_date__gte=start_date,
                                       tracker_date__lte=end_date).extra({'activity_date':"date(tracker_date)"}).values('activity_date').annotate(count=Count('id'))
    for i in range(0,no_days,+1):
        temp = start_date + datetime.timedelta(days=i)
        count = next((dct['count'] for dct in trackers if dct['activity_date'] == temp.date()), 0)
        student_activity.append([temp.strftime("%d %b %Y"),count])
        
    # get leaderboard
    leaderboard = cohort.get_leaderboard(10)
    
    
    return render_to_response('oppia/course/cohort-activity.html',
                              {'cohort':cohort,
                               'activity_graph_data': student_activity, 
                               'leaderboard': leaderboard, }, 
                              context_instance=RequestContext(request))
    
def cohort_leaderboard_view(request,cohort_id):
    
    cohort, response = can_view_cohort(request,cohort_id)
    
    if cohort is None:
        return response
        
    # get leaderboard
    lb = cohort.get_leaderboard(0)
    
    paginator = Paginator(lb, 25) # Show 25 contacts per page

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        leaderboard = paginator.page(page)
    except (EmptyPage, InvalidPage):
        leaderboard = paginator.page(paginator.num_pages)

    
    return render_to_response('oppia/course/cohort-leaderboard.html',
                              {'cohort':cohort,
                               'page':leaderboard, }, 
                              context_instance=RequestContext(request))

def cohort_edit(request,cohort_id):
    if not can_edit_cohort(request, cohort_id):
        return HttpResponse('Unauthorized', status=401)  
    cohort = Cohort.objects.get(pk=cohort_id)
    teachers_selected = []
    students_selected = []
    courses_selected = []

    if request.method == 'POST':
        form = CohortForm(request.POST)
        if form.is_valid(): 
            cohort.description = form.cleaned_data.get("description").strip()
            cohort.start_date = form.cleaned_data.get("start_date")
            cohort.end_date = form.cleaned_data.get("end_date")
            cohort.save()
            
            Participant.objects.filter(cohort=cohort).delete()
            
            students = form.cleaned_data.get("students").split(",")
            if len(students) > 0:
                for s in students:
                    try:
                        participant = Participant()
                        participant.cohort = cohort
                        participant.user = User.objects.get(username=s.strip())
                        participant.role = Participant.STUDENT
                        participant.save()
                    except User.DoesNotExist:
                        pass
            teachers = form.cleaned_data.get("teachers").split(",")
            if len(teachers) > 0:
                for t in teachers:
                    try:
                        participant = Participant()
                        participant.cohort = cohort
                        participant.user = User.objects.get(username=t.strip())
                        participant.role = Participant.TEACHER
                        participant.save()
                    except User.DoesNotExist:
                        pass
             
            CourseCohort.objects.filter(cohort=cohort).delete()       
            courses = form.cleaned_data.get("courses").strip().split(",")
            if len(courses) > 0:
                for c in courses:
                    try:
                        course = Course.objects.get(shortname=c.strip())
                        CourseCohort(cohort=cohort, course=course).save()
                    except Course.DoesNotExist:
                        pass
                    
            return HttpResponseRedirect('../../')
           
    else:
        form = CohortForm(initial={'description': cohort.description,
                                   'start_date': cohort.start_date,
                                   'end_date': cohort.end_date,
                                   })

    teachers_selected = User.objects.filter(participant__role=Participant.TEACHER, participant__cohort=cohort)
    students_selected = User.objects.filter(participant__role=Participant.STUDENT, participant__cohort=cohort)
    courses_selected = Course.objects.filter(coursecohort__cohort=cohort)

    ordering, users = get_paginated_users(request)
    c_ordering, courses = get_paginated_courses(request)

    return render(request, 'oppia/cohort-form.html',{
                            'form': form,
                            'page': users,
                            'selected_teachers': teachers_selected,
                            'selected_students': students_selected,
                            'selected_courses': courses_selected,
                            'courses_page': courses,
                            'courses_ordering': c_ordering,
                            'page_ordering':ordering,
                            'users_list_template':'select'})

def cohort_course_view(request, cohort_id, course_id): 
    cohort, response = can_view_cohort(request,cohort_id)
    if response is not None:
        return response
    
    try:
        course = Course.objects.get(pk=course_id, coursecohort__cohort=cohort)
    except Course.DoesNotExist:
        raise Http404()
    
    start_date = timezone.now() - datetime.timedelta(days=31)
    end_date = timezone.now()
    student_activity = []
    no_days = (end_date-start_date).days + 1
    users =  User.objects.filter(participant__role=Participant.STUDENT, participant__cohort=cohort).order_by('first_name', 'last_name')   
    trackers = Tracker.objects.filter(course=course, 
                                       user__is_staff=False,
                                       user__in=users,  
                                       tracker_date__gte=start_date,
                                       tracker_date__lte=end_date).extra({'activity_date':"date(tracker_date)"}).values('activity_date').annotate(count=Count('id'))
    for i in range(0,no_days,+1):
        temp = start_date + datetime.timedelta(days=i)
        count = next((dct['count'] for dct in trackers if dct['activity_date'] == temp.date()), 0)
        student_activity.append([temp.strftime("%d %b %Y"),count])
     
    students = []
    media_count = course.get_no_media()
    for user in users:
        print user
        course_stats = UserCourseSummary.objects.filter(user=user, course=course_id)
        if course_stats:
            course_stats = course_stats[0]
            data = {'user': user,
                'no_quizzes_completed': course_stats.quizzes_passed ,
                'pretest_score': course_stats.pretest_score,
                'no_activities_completed': course_stats.completed_activities,
                'no_points': course_stats.points,
                'no_badges': course_stats.badges_achieved,
                'no_media_viewed': course_stats.media_viewed,}
        else:
            #The user has no activity registered
            data = {'user': user,
                'no_quizzes_completed': 0,
                'pretest_score': 0,
                'no_activities_completed': 0,
                'no_points': 0,
                'no_badges': 0,
                'no_media_viewed': 0,}

        students.append(data)

    order_options = ['user', 'no_quizzes_completed', 'pretest_score',
                     'no_activities_completed','no_points', 'no_badges', 'no_media_viewed']
    default_order = 'user'

    ordering = request.GET.get('order_by', default_order)
    inverse_order = ordering.startswith('-')
    if inverse_order:
        ordering = ordering[1:]

    if ordering not in order_options:
        ordering = default_order
        inverse_order = False

    students.sort(key=operator.itemgetter(ordering), reverse=inverse_order)
       
    return render_to_response('oppia/course/cohort-course-activity.html',
                              {'course': course,
                               'cohort': cohort,
                               'course_media_count':media_count,
                               'activity_graph_data': student_activity,
                               'page_ordering': ('-' if inverse_order else '') + ordering,
                               'students': students }, 
                              context_instance=RequestContext(request))
       
def leaderboard_view(request):
    lb = Points.get_leaderboard()
    paginator = Paginator(lb, 25) # Show 25 per page

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        leaderboard = paginator.page(page)
    except (EmptyPage, InvalidPage):
        leaderboard = paginator.page(paginator.num_pages)

    return render_to_response('oppia/leaderboard.html',
                              {'page':leaderboard}, 
                              context_instance=RequestContext(request))

def course_quiz(request,course_id):
    course = check_owner(request,course_id)
    digests = Activity.objects.filter(section__course=course,type='quiz').order_by('section__order').distinct()
    quizzes = []
    for d in digests:
        try:
            q = Quiz.objects.get(quizprops__name='digest',quizprops__value=d.digest)
            q.section_name = d.section.title
            quizzes.append(q)
        except Quiz.DoesNotExist:
            pass
    return render_to_response('oppia/course/quizzes.html',
                              {'course': course, 
                               'quizzes':quizzes}, 
                              context_instance=RequestContext(request))

def course_quiz_attempts(request,course_id,quiz_id):
    # get the quiz digests for this course
    course = check_owner(request,course_id)
    quiz = Quiz.objects.get(pk=quiz_id)
    attempts = QuizAttempt.objects.filter(quiz=quiz).order_by('-attempt_date')
    
    paginator = Paginator(attempts, 25)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        attempts = paginator.page(page)
        for a in attempts:
            a.responses = QuizAttemptResponse.objects.filter(quizattempt=a)                
    except (EmptyPage, InvalidPage):
        tracks = paginator.page(paginator.num_pages)
    print  len(attempts)

    return render_to_response('oppia/course/quiz-attempts.html',
                              {'course': course,
                               'quiz':quiz, 
                               'page':attempts}, 
                              context_instance=RequestContext(request))

def course_feedback(request,course_id):
    course = check_owner(request,course_id)
    digests = Activity.objects.filter(section__course=course,type='feedback').order_by('section__order').values('digest').distinct()
    feedback = []
    for d in digests:
        try:
            q = Quiz.objects.get(quizprops__name='digest',quizprops__value=d['digest'])
            feedback.append(q)
        except Quiz.DoesNotExist:
            pass
        
    return render_to_response('oppia/course/feedback.html',
                              {'course': course,
                               'feedback':feedback}, 
                              context_instance=RequestContext(request))

def course_feedback_responses(request,course_id,quiz_id):
    #get the quiz digests for this course
    course = check_owner(request,course_id)
    quiz = Quiz.objects.get(pk=quiz_id)
    attempts = QuizAttempt.objects.filter(quiz=quiz).order_by('-attempt_date')
    
    paginator = Paginator(attempts, 25)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        attempts = paginator.page(page)
        for a in attempts:
            a.responses = QuizAttemptResponse.objects.filter(quizattempt=a)                
    except (EmptyPage, InvalidPage):
        tracks = paginator.page(paginator.num_pages)

    return render_to_response('oppia/course/feedback-responses.html',
                              {'course': course,
                               'quiz':quiz, 
                               'page':attempts}, 
                              context_instance=RequestContext(request))
