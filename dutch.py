import csv
import yaml
import random
import re
from pathlib import Path

from thefuzz import fuzz
from rich import print
from rich.prompt import Prompt, Confirm


class Lesson:
    def __init__(self, number) -> None:
        self._dir = Path('./lessons/{}'.format(number))

        self.left = {}
        self.right = {}
        self.questions = 0

        with open(self._dir / 'meta.yml') as metadata_file:
            self.metadata = yaml.safe_load(metadata_file)

        with open(self._dir / 'dict.csv') as wordfile:
            dialect = csv.Sniffer().sniff(wordfile.read(1024))
            wordfile.seek(0)
            reader = csv.reader(wordfile, dialect=dialect)
            next(reader)
            lines = []

            for line in reader:
                lines.append(line)
                self.questions += 1

            random.shuffle(lines)

            for line in lines:
                left, right = line[0], line[1]

                if left not in self.left:
                    self.left[left] = []

                self.left[left].append(right)

                if right not in self.right:
                    self.right[right] = []

                self.right[right].append(left)

    def quiz(self):
        test = random.choice([self.left, self.right]).copy()
        while True:
            remove = []
            count = 0
            length = len(test)
            good_answers, bad_answers, close_calls = 0, 0, 0

            for question, answers in test.items():
                count += 1
                user_answer = Prompt.ask("[{}/{}] What is '[bold yellow]{}[/bold yellow]' in {}?".format(
                    count, length, question, self.metadata['right'] if test == self.left else self.metadata['left'])).strip()
                correct = False

                for answer in answers:
                    answer = re.sub(r'\([^\(\)]+\)', '', answer).strip()
                    if answer.lower() == user_answer.lower():
                        print(' :smiley: [green]Correct[/green]')
                        correct = True
                        good_answers += 1
                        remove.append(question)
                        break
                    elif fuzz.ratio(answer.lower(), user_answer.lower()) >= 67:
                        print(
                            ' [yellow]Correct ([bold]{}[/bold])[/yellow]'.format(answer))
                        correct = True
                        close_calls += 1
                        break

                if not correct:
                    bad_answers += 1
                    print(
                        ' [red]Incorrect! Correct answers: [bold]{}[/bold][/red]'.format(','.join(answers)))

            print()
            print('Your result: [bold]{}[/bold] / [bold]{}[/bold] ({}%)'.format(
                good_answers + close_calls, length, ((good_answers + close_calls) / length) * 100.0))
            print(' [yellow] Close calls: {} [/yellow]'.format(close_calls))

            for _ in remove:
                test.pop(_)

            retry = False
            if test:
                retry = Confirm.ask(
                    'Do you want to retry your imperfect answers?')

            if not test or not retry:
                break

    def load_all():
        lessons = []
        for p in Path('./lessons/').iterdir():
            if p.is_dir():
                lessons.append(Lesson(p.name))

        return lessons


if __name__ == '__main__':
    lessons = Lesson.load_all()

    print('Lessons: ')
    for i, l in enumerate(lessons):
        print("  {}: {}".format(i + 1, l.metadata['name']))

    choice = Prompt.ask("Which lesson do you want to practice?",
                        choices=list(map(str, range(1, len(lessons) + 1))))

    lessons[int(choice) - 1].quiz()
