import builtins
from autobahn.twisted.component import Component, run
from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn.twisted.util import sleep
from autobahn.wamp.exception import ApplicationError
from datetime import datetime
from random import randint, choice

#Defines and global variables:
child_name = "Name here"
food = False
touch = False

#Loading in data for the robot
compliments = []
reminders = []
moppen = []

with open("moppen.txt", "r") as moppen_file:
	for line in moppen_file:
		moppen.append(line)

with open("reminders.txt", "r") as reminders_file:
	for line in reminders_file:
		reminders.append(line)

with open("complimenten.txt", "r") as complimenten_file:
	for line in complimenten_file:
		compliments.append(line)

#Gets next non 'done' line in routine.txt
def get_next_routine():
    with open("routines.txt", "r") as routine_file:
        data = routine_file.readlines()
    next_routine = ""
    for x in range(0, len(data)):
        li = list(data[x].strip("\n").split(";"))
        if li[-1] == "in_progress":
            return data[x], list(data[x].split(";"))[0]
        elif li[-1] == "tbd":
            data[x] = data[x].replace("tbd", "in_progress")
            next_routine = data[x]
            break
    if next_routine == "":
        return None, None
    with open("routines.txt", "w") as routine_file:
        routine_file.writelines(data)
    return next_routine, list(next_routine.split(";"))[0]

#Sets a routine as done
def routine_done(routine):
    with open("routines.txt", "r") as routine_file:
        data = routine_file.readlines()
    for x in range(0, len(data)):
        if data[x] == routine:
            data[x] = data[x].replace("in_progress", "done")
    with open("routines.txt", "w") as routine_file:
        routine_file.writelines(data)

#Adds a routine in the correct stop in a file UNUSED
def add_routine(time_and_day, list_of_tasks):
	datetime_date = datetime.strptime(time_and_day, "%d/%m-%H:%M")
	tasks_string = ""
	for task in list_of_tasks:
		tasks_string += task + ";"
	with open("routines.txt", "r") as routine_file:
		data = routine_file.readlines()
		inserted = False
	if datetime.strptime(list(data[0].split(";"))[0],"%d/%m-%H:%M") > datetime_date and not inserted:
		data.insert(0, time_and_day + ";" + tasks_string + "tbd\n")
		inserted = True
	if datetime.strptime(list(data[-1].split(";"))[0],"%d/%m-%H:%M") < datetime_date and not inserted:
		data.append(time_and_day + ";" + tasks_string + "tbd\n")
		inserted = True
	for x in range(0, len(data)):
		if datetime.strptime(list(data[x-1].split(";"))[0],"%d/%m-%H:%M") < \
                datetime_date < datetime.strptime(list(data[x].split(";"))[0],"%d/%m-%H:%M") \
                and not inserted:
			data.insert(x, time_and_day + ";" + tasks_string + "tbd\n")
			inserted = True
	with open("routines.txt", "w") as routine_file:
		routine_file.writelines(data)

#Define what to do when head is touched
def touched(frame):
	global touch
	if (("body.head.front" in frame["data"] and frame["data"]["body.head.front"]) or
			("body.head.middle" in frame["data"] and frame["data"]["body.head.middle"]) or
			("body.head.rear" in frame["data"] and frame["data"]["body.head.rear"])):
		touch = True

#Listens to keywords
def done(frame):
	global sess
	global klaar
	print(frame["data"]["body"]["text"])
	if "klaar" in frame["data"]["body"]["text"] \
			or "check" in frame["data"]["body"]["text"]\
			or "gehoord" in frame["data"]["body"]["text"]\
			or "gedaan" in frame["data"]["body"]["text"]\
			or "gelukt" in frame["data"]["body"]["text"]:
		klaar = True

#Definition of difrent tasks inroutine.txt or uses default if nothing is defined
@inlineCallbacks
def define_task(session, task):
	global touch, child_name, food
	remind_timer = 60
	if task == "tanden poetsen":
		yield speak(session, "de volgende taak is tanden poetsen. Tik op mijn hoofd als je klaar staat om je tanden te poetsen.")
		touch = False
		counter = 1
		while not touch:
			if counter % 20 == 0:
				yield speak(session, "Tik op mijn hoofd als je klaar staat om je tanden te poetsen.")
			yield sleep(0.5)
			counter += 0.5
		touch = False
		yield speak(session, "Oké de twee minuten beginnen nu, poetsen maar!")
		yield sleep(30)
		yield speak(session, "Er zijn al 30 seconde voorbij")
		yield sleep(30)
		yield speak(session, "Nog 1 minuut")
		yield sleep(30)
		yield speak(session, "nog 30 seconden")
		yield sleep(15)
		yield speak(session, "nog maar 15 seconden")
		yield sleep(15)
		yield speak(session, "Dat waren de twee minuten! Zeg klaar om naar de volgende taak door te gaan")
		return 15
	elif task == "opstaan":
		yield speak(session, "Goedenmorgen " + child_name + " het is tijd om op te staan, tik op mijn hoofd om de wekker uit te zetten.")
		counter = 0
		touch = False
		while not touch:
			yield sleep(0.5)
			if counter%16 == 0:
				yield session.call("rom.optional.behavior.play", name="BlocklySaxophone", sync=False)
			counter += 1
		yield session.call("rom.optional.behavior.stop")
		remind_timer = 15
	elif task == "avondeten":
		yield speak(session, "Het is tijd voor het avondeten " + child_name + ", zeg klaar als hebt gegeten en eet smakelijk!")
		return 600
	elif task == "lunch":
		yield speak(session, "Het is tijd om te lunchen " + child_name + ", zeg klaar als je me gehoord hebt")
		food = True
		return 15
	elif task == "ontbijt":
		yield speak(session, "Het is tijd om te ontbijten " + child_name + ", zeg klaar als je me gehoord hebt")
		food = True
		return 15
	elif task == "naar bed":
		yield speak(session, "Het is bedtijd, slaap lekker en vergeet niet om nog even klaar te zeggen zodat ik weet dat je me hebt gehoord")
		return remind_timer
	elif task == "trompet oefenen":
		yield speak(session, "De volgende taak is trompet oefenen, zeg klaar als je klaar bent om te oefenen.")
		return 15
	elif task == "ontspanning":
		yield speak(session, "Oké " + child_name + " je kan nu even lekker ontspannen en iets voor jezelf doen. Zeg wel nog even klaar zodat ik weet dat je me hebt gehoord")
		return remind_timer
	else:
		yield speak(session, "Oké " + child_name + ". De volgende taak is " + task)
	yield speak(session, "Laat het weten als " + task + " is gelukt")
	return remind_timer

#Runs through a task.
@inlineCallbacks
def do_task(session, task):
	yield session.call("rom.optional.behavior.play", name="BlocklyStand", sync=False)
	global klaar, reminders, compliments, reminders, touch, food
	result = yield define_task(session, task)
	yield session.subscribe(done, "rie.dialogue.stt.stream")
	yield session.call("rie.dialogue.stt.stream")
	klaar = False
	touch = False
	counter = 1
	while not klaar and not touch:
		yield sleep(0.5)
		if counter%(result*2) == 0:
			yield session.call("rie.dialogue.stt.close")
			yield speak(session, "Herinering de huidige taak is: " + task + " Zeg klaar als " + task + " is gedaan")
			yield session.call("rie.dialogue.stt.stream")
		if counter%(result) == 0:
			yield session.call("rie.dialogue.stt.close")
			if food:
				yield speak(session, "Zeg klaar als je me gehoord hebt en klaar bent voor " + task)
			else:
				yield speak(session, choice(reminders))
			yield session.call("rie.dialogue.stt.stream")
		counter += 0.5
	if food:
		yield speak(session, "Eet smakelijk!")
		food = False
	else:
		yield speak(session, choice(compliments))
	yield session.call("rie.dialogue.stt.close")

#special function for packing a bag
@inlineCallbacks
def packing_bag(session, items):
	yield session.call("rom.optional.behavior.play", name="BlocklyStand", sync=False)
	global klaar, child_name
	yield speak(session, "Oké " + child_name + " het is tijd om je tas in te pakken! Ik noem iets wat in je tas moet, als het erinzit roep je check")
	yield session.subscribe(done, "rie.dialogue.stt.stream")
	yield session.call("rie.dialogue.stt.stream")
	for item in items:
		yield speak(session, item)
		klaar = False
		counter = 15
		while not klaar:
			counter += 0.5
			yield sleep(0.5)
			if counter%30 == 0:
				yield session.call("rie.dialogue.stt.close")
				yield speak(session, "is het al gelukt om " + item + " in te pakken? Vergeet dan niet check te roepen!")
				yield session.call("rie.dialogue.stt.stream")
	yield session.call("rie.dialogue.stt.close")
	yield speak(session, choice(compliments))

#special function for getting dressed
@inlineCallbacks
def getting_dressed(session, items):
	yield session.call("rom.optional.behavior.play", name="BlocklyStand", sync=False)
	global klaar, child_name
	yield speak(session, "Oké " + child_name + " het is tijd om je aan te kleden! Ik noem een kleding stuk, als je het aanhebt roep je check!")
	yield session.subscribe(done, "rie.dialogue.stt.stream")
	yield session.call("rie.dialogue.stt.stream")
	for item in items:
		yield speak(session, item)
		klaar = False
		counter = 15
		while not klaar:
			counter += 0.5
			yield sleep(0.5)
			if counter%30 == 0:
				yield session.call("rie.dialogue.stt.close")
				yield speak(session, "is het al gelukt om " + item + " aan te trekken? Vergeet dan niet check te roepen!")
				yield session.call("rie.dialogue.stt.stream")
	yield session.call("rie.dialogue.stt.close")
	yield speak(session, choice(compliments))

#Basic function to call for speach
@inlineCallbacks
def speak(session, text):
	yield session.call("rie.dialogue.say_animated", text=text, lang="nl")

#Main loop waiting for tasks and looping through routines
@inlineCallbacks
def main(session, details):
	global sess, touch, child_name
	sess = session
	yield session.call("rom.optional.behavior.play", name="BlocklyCrouch", sync=True)
	yield session.subscribe(touched, "rom.sensor.touch.stream")
	yield session.call("rom.sensor.touch.stream")
	next_routine, next_routine_start = get_next_routine()
	while next_routine != None:
		if datetime.strptime("2024" + next_routine_start, "%Y%d/%m-%H:%M") < datetime.now():
			print("Routine begonnen")
			for task in list(next_routine.split(";")[1:-1]):
				print(task + " Begonnen")
				if task[:8] == "paklijst":
					yield packing_bag(session, task[9:].split("-"))
				if task[:9] == "aankleden":
					yield getting_dressed(session, task[9:].split("-"))
				else:
					yield do_task(session, task)
				print(task + " Gedaan")
			print("Routine klaar")
			routine_done(next_routine)
			next_routine, next_routine_start = get_next_routine()
			try:
				yield speak(session, "Dat was alles voor nu! De volgende taak is: " + next_routine.split(";")[1].split("-")[0] +
						" en begint om " + next_routine_start[6:] + ".")
				if randint(0,4) == 0:
					yield speak(session, "Vergeet niet om me aan de oplader te hangen!")
			except builtins.AttributeError:
				pass
			yield session.call("rom.optional.behavior.play", name="BlocklyCrouch", sync=True)
			touch = False
		if touch:
			print("Grap vertelt")
			yield speak(session, choice(moppen))
			touch = False
		yield sleep(0.1)

	yield speak(session, "Alle taken zijn gedaan! Ik sluit af.")
	session.leave()

#Setting up the connection, change the realm according to the one found on 'robots in de klas'
wamp = Component(
	transports=[{
		"url": "ws://wamp.robotsindeklas.nl",
		"serializers": ["msgpack"],
		"max_retries": 0
	}],
	realm="rie.6655a67cf26645d6dd2c1ea9",
)

wamp.on_join(main)

if __name__ == "__main__":
	run([wamp])
