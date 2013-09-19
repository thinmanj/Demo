# Create your views here.
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
import datetime
import csv
from models import File, Team, Metric, TeamMember, MetricData
from django.views.decorators.csrf import csrf_exempt
from django.utils import simplejson
from django.db.models import Sum
import gspread

class SimpleFileForm(forms.Form):
    file = forms.Field(widget=forms.FileInput, required=False)

messages = []

#Settings for csv parssing

teamName = 0
metricName = 1
oDeskName = 0
memberName = 1
dateStart = 2


def datetime_from_str(time_str):
    #
    # Try to parse string into date object
    #
    date = time_str.split('/')
    if len(date)<3:
        messages.append("%s isn't in correct format " % time_str)
        raise
    #
    # Letting Date parse infstructure
    #
    try:
        date = datetime.date(int(date[2]),int(date[0]), int(date[1]))
    except:
        messages.append("%s could not parsed correctly " % time_str)
        raise
    #    
    # weekday should be 6 for sunday
    #
    if not date.weekday() == 6:
        messages.append('date: %s is not sunday' % date)
        raise
    return date

#
# Uploda data from csv files
#


def csvUpload(request):
    global messages
    messages = []
    try:
        template = 'fileupload.html'
        form = SimpleFileForm()
     
        if request.method == 'POST':
            if 'file' in request.FILES:


                #
                # Final counters
                #
                numberWeeks = 0
                numberTeamMembers = 0
                numberActuals = 0

                #
                # Preprossesing file 
                #
                csvfile = request.FILES['file']

                fileName = csvfile.name
                fileSize = csvfile.size
                rawData = csvfile.read()
                csvfile.seek(0)
                csvData = csv.reader(csvfile)
                fileDate = datetime.datetime.now()

                #
                # create file record
                #

                try:
                    f = File(name=fileName, uploadDate=fileDate, data=rawData, 
                        status="This message means an internal error...")
                    f.save()
                    messages.append('Loaded file: "%s" [%d] on %s '% (fileName, fileSize, fileDate))
                except:
                    messages.append('Error while saving csv file')
                    raise
                #
                # parse csv data
                #

                teamHead = []
                teamData = {}

                teamMemberHead = []

                for row in csvData:
                    if not teamData:
                        if not teamHead:
                            #
                            # Working on Team and Metric Header
                            #

                            teamHead = row
                            
                            #
                            # Testing team data 
                            #
                            if len(teamHead)<2:
                                messages.append('Team Header row 1 has less than  expected data')

                            if teamHead[teamName] != "Team Name":
                                messages.append('Expected Team Name Header not found')

                            if teamHead[metricName] != "Metric Name":
                                messages.append('Expected Metric Name Header not found')


                        else:
                            #
                            # Working on Team and Metric names
                            #

                            #
                            # testing team data 
                            #
                            if len(row)<2:
                                messages.append('Error, Team Data has less than expected data')
                                raise 
                            #
                            # Get Team and Metric objects
                            #

                            try:
                                team, created = Team.objects.get_or_create(name=row[0])
                                #team.save()
                            except:
                                messages.append('Error with team information')
                                raise
                            try:
                                metric, created = Metric.objects.get_or_create(team=team, name=row[1])
                                #metric.save()
                            except:
                                messages.append('Error with metric information')
                                raise

                            teamData['team'] = team
                            teamData['metric'] = metric
                    else:
                        #
                        # Working on member an metrics data
                        #

                        if not teamMemberHead:
                            #
                            # Testing second Header
                            #

                            teamMemberHead = row

                            if len(teamMemberHead)<dateStart+1:
                                messages.append('Team Member row 3 has less than expected data')

                            if teamMemberHead[oDeskName] != "oDesk ID":
                                messages.append('Expected oDesk ID Header not found')

                            if teamMemberHead[memberName] != "Member Name":
                                messages.append('Expected Member Name Header not found')

                            #
                            # Processing dates from header
                            #

                            try:
                                metricDates = map(datetime_from_str, teamMemberHead[dateStart:])
                                numberWeeks = len(metricDates)
                            except:
                                messages.append('Some dates could not be parsed or are not sundays')
                                raise
                        else:
                            # 
                            # Processing each memeber data
                            #

                            numberTeamMembers += 1
                            try:
                                teamMember, created = TeamMember.objects.get_or_create(team=team, oId = row[oDeskName], 
                                    defaults={'name': row[memberName]})
                            except:
                                messages.append('Erro while getting Team member.')
                                raise

                            #
                            # Processing members metrics
                            #

                            try:
                                for metricDate, metricValue in zip(metricDates, row[dateStart:]):
                                    metdef ={'fileLoaded':f}
                                    if not metricValue:
                                        metdef['value'] = 0
                                        metdef['status'] = False
                                    else:
                                        metdef['value'] = int(metricValue)
                                    MetricData.objects.get_or_create(member=teamMember, metric=metric, metricDate=metricDate,
                                        defaults=metdef)
                                    numberActuals +=1
                            except:
                                messages.append('Erro while inserting Metric.')
                                raise


                #
                # Saving final file status 
                #
                messages.append("team='%s' metric='%s' processed %d actuals. %d members by %d weeks."%
                    (team.name, metric.name, numberActuals, numberTeamMembers, numberWeeks))
                f.status = "\n".join(messages)
                f.save()
            else:

                messages.append('No file attached')
     
            return render_to_response(template, RequestContext(request, {
                'form': form,
                'processMessages': messages,
                }))
        else:
            #
            # Display the form
            #

            return render_to_response(template, RequestContext(request, {
                'form': form,
                'processMessages': messages,
                }))
    except:
        #
        # Here we hold every problem genenrated on parsing
        #
        try:
            if f:
                f.status = "\n".join(messages)
                f.save()
        except:
            #
            #  Let's display them......
            #
            pass
        return render_to_response(template, RequestContext(request, {
            'form': form,
            'processMessages': messages,
            }))

#
# Update a Google Spreedsheet
#
class UpdateGoogleForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    spreadsheet = forms.CharField()
    worksheet = forms.CharField()



def updateGoogle(request):
    processMessages = []
    if request.method == "POST":
        form = UpdateGoogleForm(request.POST)
        if form.is_valid():
            try:
                gc = gspread.login(form.cleaned_data['email'], form.cleaned_data['password'])
                spreadsheet = gc.open(form.cleaned_data['spreadsheet'])
                worksheet = spreadsheet.worksheet(form.cleaned_data['worksheet'])
            except:
                processMessages.append('Error acccesing google')

            row = 3

            for metric in Metric.objects.all():
                #print metric
                data = [metric.team.name, metric.name, metric.completed_units(), metric.cost_per_unit(),
                        metric.unit_cost_goal(), metric.hours_per_task(), metric.team_size(), 
                        metric.description, metric.expectedValue, metric.hourlyRate, 
                        metric.team_size(), metric.four_week_cost(), metric.annual_cost(), 
                        metric.high_result(), metric.average_result(), metric.low_result()]
                data = zip(range(16), data)
                try:
                    for i, field in data:
                        worksheet.update_cell(row, i+1, field)
                except:
                    processMessages.append('Problems accesing spreadsheet')
                row += 1

            processMessages.append('Procesado')

            return render_to_response('update.html',RequestContext(request, {
                'form': form,
                'processMessages': processMessages,
                }))
    else:
        form = UpdateGoogleForm()
    
    return render_to_response('update.html',RequestContext(request, {
                'form': form,
                'processMessages': processMessages,
                }))

#
# Display Team
#
class TeamSelectForm(forms.Form):
    team = forms.ModelChoiceField(Team.objects.all())
    weekend = forms.ChoiceField(choices=[])
    #dateSelect = forms.ChoiceField(choices=get_weekends())
    
    def __init__(self, *args, **kwargs):
        super(TeamSelectForm, self).__init__(*args, **kwargs)
        dataDate = []
        td = datetime.date.today()
        fd = td+datetime.timedelta(6-td.weekday())-datetime.timedelta(7*13)
    
        for delta in range(91,0,-7):
            pd = fd+datetime.timedelta(delta)
            dataDate.append([pd.strftime("%m/%d/%Y"),pd])

        self.fields['weekend'].choices=dataDate

def dateSpan(toDate):
    #
    # To get the 4 week span
    #
    delta = datetime.timedelta(21)
    fromDate = toDate - delta
    return fromDate, toDate

def displayTeam(request):
    if request.method == "POST":
        form = TeamSelectForm(request.POST)
        if form.is_valid():
            #
            # Get dates
            #

            fromDate, toDate = dateSpan(datetime_from_str(form.cleaned_data['weekend']))
            delta = datetime.timedelta(7)
            secondDate = fromDate+delta
            thirdDate = toDate-delta
            teamData = {}
            teamData['header'] = {
                'week1':fromDate.strftime("%m/%d/%Y"),
                'week2':secondDate.strftime("%m/%d/%Y"),
                'week3':thirdDate.strftime("%m/%d/%Y"),
                'week4':toDate.strftime("%m/%d/%Y"),
            }

            #
            # Get Team data
            #

            teamData['team'] = []
            consolidate = {}
            for memberData in MetricData.objects.filter(status=True).filter(value__gt=0).filter(metricDate__range=(fromDate, toDate)).filter(member__team=form.cleaned_data['team']).values('member__name').annotate(total=Sum('value')).order_by('-total'):

                #
                # get Total and sort by
                #
                elem = {'name':memberData['member__name'], 'total':memberData['total'], 'week1':0, 'week2':0, 'week3':0, 'week4':0,}
                consolidate[memberData['member__name']] = elem

                teamData['team'].append(elem)

            #
            # Get individual data
            #

            for member in MetricData.objects.filter(status=True).filter(metricDate__range=(fromDate, toDate)).filter(member__team=form.cleaned_data['team']).values('member__name','metricDate', 'value').order_by('member__name').all():
                name = member['member__name']
                try:
                    elem = consolidate[name]
                    if member['metricDate'] == fromDate:
                        elem['week1'] = member['value']
                    elif member['metricDate'] == secondDate:
                        elem['week2'] = member['value']
                    elif member['metricDate'] == thirdDate:
                        elem['week3'] = member['value']
                    else:
                        elem['week4'] = member['value']

                except:
                    pass

            return render_to_response('displayTeam.html',RequestContext(request, {
                'form': form,
                'teamData': teamData,
                }))
    else:
        form = TeamSelectForm()
    
    return render_to_response('displayTeam.html',RequestContext(request, {
        'form': form,
        }))

#
# test for a json view
#
@csrf_exempt
def webAPI(request):
    messages = []


    try:
        if request.is_ajax() or request.method == 'POST':
        #if request.method == 'POST': # just for testing Don't know if there is a problem with is_ajax on django
            try:
                data = simplejson.loads(request.raw_post_data)
            except:
                messages.append('Json bad formated')

            try:
                team = Team.objects.get(name=data.get('team', ''))
            except:
                messages.append('Error with team information')

            try:
                metric = Metric.objects.get(team=team, name=data.get('metric', ''))
            except:
                messages.append('Error with metric information')

            try:
                memeber = TeamMember.objects.get(team=team, name=data.get('member', ''))
            except:
                messages.append('Error with member information')

            try:
                date = datetime_from_str(data.get('date', ''))
            except:
                messages.append('Error with date information')

            try:
                value = data.get('value', '')
                MetricData.objects.get_or_create(member=member, metric=metric, metricDate=metricDate, default={'value':int(value)})
                messages.append('Metric Saved')
            except:
                messages.append('Error while saving metric')
        else:
            messages.append('This should be called like an ajax service')
    except:
        pass

    return render_to_response('postajax.html', locals())

