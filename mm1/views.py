from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import *
import random as rnd
from. forms import *
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from bs4 import BeautifulSoup
from newspaper import Article

POPULATION_SIZE = 9
NUMB_OF_ELITE_SCHEDULES = 1
TOURNAMENT_SELECTION_SIZE = 3
MUTATION_RATE = 0.05


class Data:
    def __init__(self):
        self._rooms = Room.objects.all()
        self._meetingTimes = MeetingTime.objects.all()
        self._instructors = Instructor.objects.all()
        self._courses = Course.objects.all()
        self._depts = Department.objects.all()

    def get_rooms(self): return self._rooms

    def get_instructors(self): return self._instructors

    def get_courses(self): return self._courses

    def get_depts(self): return self._depts

    def get_meetingTimes(self): return self._meetingTimes


class Schedule:
    def __init__(self):
        self._data = data
        self._classes = []
        self._numberOfConflicts = 0
        self._fitness = -1
        self._classNumb = 0
        self._isFitnessChanged = True

    def get_classes(self):
        self._isFitnessChanged = True
        return self._classes

    def get_numbOfConflicts(self): return self._numberOfConflicts

    def get_fitness(self):
        if self._isFitnessChanged:
            self._fitness = self.calculate_fitness()
            self._isFitnessChanged = False
        return self._fitness

    def initialize(self):
        sections = Section.objects.all()
        for section in sections:
            dept = section.specialization
            n = section.num_appointments_in_week
            if n <= len(MeetingTime.objects.all()):
                courses = dept.patients.all()
                for course in courses:
                    for i in range(n):
                        crs_inst = course.doctors.all()
                        newClass = Class(self._classNumb, dept, section.section_id, course)
                        self._classNumb += 1
                        newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
                        newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
                        newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
                        self._classes.append(newClass)
            else:
                n = len(MeetingTime.objects.all())
                courses = dept.patients.all()
                for course in courses:
                    for i in range(n):
                        crs_inst = course.doctors.all()
                        newClass = Class(self._classNumb, dept, section.section_id, course)
                        self._classNumb += 1
                        newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
                        newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
                        newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
                        self._classes.append(newClass)

        return self

    def calculate_fitness(self):
        self._numberOfConflicts = 0
        classes = self.get_classes()
        for i in range(len(classes)):
            if classes[i].room.numb_cabins_per_room < 3:
                self._numberOfConflicts += 1
            for j in range(len(classes)):
                if j >= i:
                    if (classes[i].meeting_time == classes[j].meeting_time) and \
                            (classes[i].section_id != classes[j].section_id) and (classes[i].section == classes[j].section):
                        if classes[i].room == classes[j].room:
                            self._numberOfConflicts += 1
                        if classes[i].instructor == classes[j].instructor:
                            self._numberOfConflicts += 1
        return 1 / (1.0 * self._numberOfConflicts + 1)


class Population:
    def __init__(self, size):
        self._size = size
        self._data = data
        self._schedules = [Schedule().initialize() for i in range(size)]

    def get_schedules(self):
        return self._schedules


class GeneticAlgorithm:
    def evolve(self, population):
        return self._mutate_population(self._crossover_population(population))

    def _crossover_population(self, pop):
        crossover_pop = Population(0)
        for i in range(NUMB_OF_ELITE_SCHEDULES):
            crossover_pop.get_schedules().append(pop.get_schedules()[i])
        i = NUMB_OF_ELITE_SCHEDULES
        while i < POPULATION_SIZE:
            schedule1 = self._select_tournament_population(pop).get_schedules()[0]
            schedule2 = self._select_tournament_population(pop).get_schedules()[0]
            crossover_pop.get_schedules().append(self._crossover_schedule(schedule1, schedule2))
            i += 1
        return crossover_pop

    def _mutate_population(self, population):
        for i in range(NUMB_OF_ELITE_SCHEDULES, POPULATION_SIZE):
            self._mutate_schedule(population.get_schedules()[i])
        return population

    def _crossover_schedule(self, schedule1, schedule2):
        crossoverSchedule = Schedule().initialize()
        for i in range(0, len(crossoverSchedule.get_classes())):
            if rnd.random() > 0.5:
                crossoverSchedule.get_classes()[i] = schedule1.get_classes()[i]
            else:
                crossoverSchedule.get_classes()[i] = schedule2.get_classes()[i]
        return crossoverSchedule

    def _mutate_schedule(self, mutateSchedule):
        schedule = Schedule().initialize()
        for i in range(len(mutateSchedule.get_classes())):
            if MUTATION_RATE > rnd.random():
                mutateSchedule.get_classes()[i] = schedule.get_classes()[i]
        return mutateSchedule

    def _select_tournament_population(self, pop):
        tournament_pop = Population(0)
        i = 0
        while i < TOURNAMENT_SELECTION_SIZE:
            tournament_pop.get_schedules().append(pop.get_schedules()[rnd.randrange(0, POPULATION_SIZE)])
            i += 1
        tournament_pop.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
        return tournament_pop


class Class:
    def __init__(self, id, dept, section, course):
        self.section_id = id
        self.department = dept
        self.course = course
        self.instructor = None
        self.meeting_time = None
        self.room = None
        self.section = section

    def get_id(self): return self.section_id

    def get_dept(self): return self.department

    def get_course(self): return self.course

    def get_instructor(self): return self.instructor

    def get_meetingTime(self): return self.meeting_time

    def get_room(self): return self.room

    def set_instructor(self, instructor): self.instructor = instructor

    def set_meetingTime(self, meetingTime): self.meeting_time = meetingTime

    def set_room(self, room): self.room = room


data = Data()


def context_manager(schedule):
    classes = schedule.get_classes()
    context = []
    cls = {}
    for i in range(len(classes)):
        cls["section"] = classes[i].section_id
        cls['dept'] = classes[i].department.spec_name
        cls['course'] = f'{classes[i].course.patient_name} ({classes[i].course.patient_number}'
        cls['room'] = f'{classes[i].room.r_number} ({classes[i].room.numb_cabins_per_room})'
        cls['instructor'] = f'{classes[i].instructor.name} ({classes[i].instructor.did})'
        cls['meeting_time'] = [classes[i].meeting_time.pid, classes[i].meeting_time.day, classes[i].meeting_time.time]
        context.append(cls)
    return context


def home(request):
    return render(request, 'index.html', {})


def timetable(request):
    schedule = []
    population = Population(POPULATION_SIZE)
    generation_num = 0
    population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
    geneticAlgorithm = GeneticAlgorithm()
    while population.get_schedules()[0].get_fitness() != 1:
        generation_num += 1
        print('\n> Generation #' + str(generation_num))
        population = geneticAlgorithm.evolve(population)
        population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
        schedule = population.get_schedules()[0].get_classes()

    return render(request, 'timetable.html', {'schedule': schedule, 'sections': Section.objects.all(),
                                              'times': MeetingTime.objects.all()})



def add_instructor(request):
    form = InstructorForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addinstructor')
    context = {
        'form': form
    }
    return render(request, 'adins.html', context)


def inst_list_view(request):
    context = {
        'doctors': Instructor.objects.all()
    }
    return render(request, 'instlist.html', context)


def delete_instructor(request, pk):
    inst = Instructor.objects.filter(pk=pk)
    if request.method == 'POST':
        inst.delete()
        return redirect('editinstructor')


def add_room(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addroom')
    context = {
        'form': form
    }
    return render(request, 'addrm.html', context)


def room_list(request):
    context = {
        'rooms': Room.objects.all()
    }
    return render(request, 'rmlist.html', context)


def delete_room(request, pk):
    rm = Room.objects.filter(pk=pk)
    if request.method == 'POST':
        rm.delete()
        return redirect('editrooms')


def meeting_list_view(request):
    context = {
        'meeting_times': MeetingTime.objects.all()
    }
    return render(request, 'mtlist.html', context)


def add_meeting_time(request):
    form = MeetingTimeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addmeetingtime')
        else:
            print('Invalid')
    context = {
        'form': form
    }
    return render(request, 'addmt.html', context)


def delete_meeting_time(request, pk):
    mt = MeetingTime.objects.filter(pk=pk)
    if request.method == 'POST':
        mt.delete()
        return redirect('editmeetingtime')


def course_list_view(request):
    context = {
        'patients': Course.objects.all()
    }
    return render(request, 'crslist.html', context)


def add_course(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addcourse')
        else:
            print('Invalid')
    context = {
        'form': form
    }
    return render(request, 'adcrs.html', context)


def delete_course(request, pk):
    crs = Course.objects.filter(pk=pk)
    if request.method == 'POST':
        crs.delete()
        return redirect('editcourse')


def add_department(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('adddepartment')
    context = {
        'form': form
    }
    return render(request, 'addep.html', context)


def department_list(request):
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'deptlist.html', context)


def delete_department(request, pk):
    dept = Department.objects.filter(pk=pk)
    if request.method == 'POST':
        dept.delete()
        return redirect('editdepartment')


def add_section(request):
    form = SectionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addsection')
    context = {
        'form': form
    }
    return render(request, 'addsec.html', context)


def section_list(request):
    context = {
        'sections': Section.objects.all()
    }
    return render(request, 'seclist.html', context)


def delete_section(request, pk):
    sec = Section.objects.filter(pk=pk)
    if request.method == 'POST':
        sec.delete()
        return redirect('editsection')
    

DATA_FILE = 'data_base.json'

def chat(request):
    context = {
        'example_data': 'Hello from the chat view!',
    }

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '')

        response_data = get_rule_based_response(user_message)

        return JsonResponse(response_data)

    return render(request, 'chat.html', context)


def get_rule_based_response(user_message):
    rules = load_rules()
    if "admin" in user_message.lower():
        return {'message': "Admin commands are /p [msg] for adding pattern and /r [msg] for adding response after pattern"}
    
    if user_message[0] == '/':
        for rule in rules:
            if rule['pattern'].lower() == "admin":
                if user_message[1] == 'p':
                    if rule['response'] == '':
                        new_rule = {'pattern': user_message[3:], 'response': "Admin please add a pattern first"}
                        rules.append(new_rule)
                        rule['response'] = user_message[3:]
                        update_rules(rules)
                        return {'message': "Updated Knowledge Base - pattern added, add response next"}
                    else:
                        return {'message': "Add response before adding new pattern"}
                    
                elif user_message[1] == 'r':
                    if rule['response'] == '':
                        return {'message': "Admin please add a pattern first"}
                    else:
                        for ruless in rules:
                            if ruless['response'] == "Admin please add a pattern first":
                                ruless['response'] = user_message[3:]
                                rule['response'] = ''
                                update_rules(rules)
                                return {'message': "Updated Knowledge Base - response added"}
                else:
                    return {'message': "Wrong command,admin. Did you forget them? :( Type admin for commands"}

    else:
        for rule in rules:
            if rule['pattern'].lower() in user_message.lower():
                return {'message': rule['response']}
        top_text,search_result = perform_internet_search(user_message)
        return {'message': f'Search result: {top_text}. \nLink: {search_result}'}
    

def perform_internet_search(query):
    search_url = f'https://duckduckgo.com/html/?q={query}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('a', {'class': 'result__a'})
        top_text = ''
        link = ''

        if search_results:
            for result in search_results:
                link = result.get('href')
                if not is_advertisement(link):
                    article = Article(link)
                    article.download()
                    article.parse()
                    page_content = article.text

                    relevant_content = page_content.strip()

                    response_lines = relevant_content.split('\n')[:10]
                    trimmed_response = '\n'.join(response_lines)

                    return trimmed_response, link

            return "No relevant search results found.", ''

        else:
            return "No search results found.", ''
    except Exception as e:
        print(f"Error: {e}")
        return "My internet is down", ''


def is_advertisement(link):
    return 'ad_domain' in link or 'ad_provider' in link


def load_rules():
    try:
        with open(DATA_FILE, 'r') as file:
            rules = json.load(file)
    except FileNotFoundError:
        rules = []
    return rules

def update_rules(rules):
    with open(DATA_FILE, 'w') as file:
        json.dump(rules, file, indent=2)

