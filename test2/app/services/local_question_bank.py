from __future__ import annotations

import random
from typing import Any

from app.adaptive import DIFFICULTY_MULTIPLIERS, pick_question_mix

TOPIC_LABELS = {
    "algebra": "Algebra",
    "calculus": "Calculus",
    "geometry": "Geometry",
    "statistics": "Statistics",
    "trigonometry": "Trigonometry",
    "arithmetic": "Arithmetic",
}


class LocalMathGenerator:
    def generate_quiz(
        self,
        *,
        topic: str,
        education_level: str,
        target_difficulty: str,
        question_count: int,
    ) -> dict[str, Any]:
        rng = random.Random()
        topic_key = (topic or "algebra").strip().lower()
        mix = pick_question_mix(target_difficulty, question_count)
        questions = []

        for index, difficulty in enumerate(mix, start=1):
            question = self._build_question(
                topic=topic_key,
                education_level=education_level,
                difficulty=difficulty,
                rng=rng,
                question_number=index,
            )
            question["difficulty"] = difficulty
            question["estimated_time_sec"] = {"easy": 45, "medium": 70, "hard": 95}[difficulty]
            questions.append(question)

        return {
            "quizTitle": f"{TOPIC_LABELS.get(topic_key, 'Math')} Skill Check",
            "introMessage": f"A {education_level.lower()} set tuned around {target_difficulty} difficulty.",
            "questions": questions,
            "source": "local-fallback",
        }

    def _build_question(
        self,
        *,
        topic: str,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        generator = {
            "algebra": self._algebra_question,
            "calculus": self._calculus_question,
            "geometry": self._geometry_question,
            "statistics": self._statistics_question,
            "trigonometry": self._trigonometry_question,
            "arithmetic": self._arithmetic_question,
        }.get(topic, self._algebra_question)

        return generator(
            education_level=education_level,
            difficulty=difficulty,
            rng=rng,
            question_number=question_number,
        )

    def _arithmetic_question(
        self,
        *,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        if difficulty == "easy":
            a = rng.randint(18, 64)
            b = rng.randint(11, 37)
            correct = a + b
            prompt = f"What is {a} + {b}?"
            explanation = f"Add tens and ones: {a} + {b} = {correct}."
            hints = ["Start by adding the tens.", "Then add the ones to finish the total."]
            distractors = [correct - 1, correct + 2, correct + 10]
            skill_tag = "Addition fluency"
        elif difficulty == "medium":
            base = rng.choice([24, 36, 48, 60, 72, 84])
            percent = rng.choice([25, 50, 75])
            correct = (base * percent) // 100
            prompt = f"What is {percent}% of {base}?"
            explanation = f"Convert {percent}% to a fraction and multiply: {percent}/100 x {base} = {correct}."
            hints = ["Turn the percent into a fraction over 100.", "Multiply and simplify."]
            distractors = [correct + 6, correct - 6, correct + base // 12]
            skill_tag = "Percent reasoning"
        else:
            a = rng.randint(8, 18)
            b = rng.randint(3, 7)
            c = rng.randint(5, 14)
            correct = (a + b) * c
            prompt = f"Evaluate ({a} + {b}) x {c}."
            explanation = f"Work inside parentheses first: {a} + {b} = {a + b}, then multiply by {c} to get {correct}."
            hints = ["Parentheses come first.", "After adding, multiply the result by the outside number."]
            distractors = [a + (b * c), correct - c, correct + b]
            skill_tag = "Order of operations"

        return self._build_choice_question(
            prompt=prompt,
            correct=str(correct),
            distractors=[str(item) for item in distractors],
            explanation=explanation,
            hints=hints,
            skill_tag=skill_tag,
            question_number=question_number,
            rng=rng,
        )

    def _algebra_question(
        self,
        *,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        if difficulty == "easy":
            x_value = rng.randint(4, 15)
            offset = rng.randint(3, 10)
            total = x_value + offset
            prompt = f"Solve for x: x + {offset} = {total}"
            explanation = f"Undo the +{offset} by subtracting {offset} from both sides: x = {total - offset}."
            hints = ["Subtract the same number from both sides.", "Isolate x by itself."]
            distractors = [str(x_value + 1), str(total), str(offset)]
            correct = str(x_value)
            skill_tag = "One-step equations"
        elif difficulty == "medium":
            x_value = rng.randint(3, 11)
            coefficient = rng.randint(2, 5)
            offset = rng.randint(4, 12)
            total = (coefficient * x_value) + offset
            prompt = f"Solve for x: {coefficient}x + {offset} = {total}"
            explanation = (
                f"Subtract {offset} first to get {coefficient}x = {total - offset}, "
                f"then divide by {coefficient} so x = {x_value}."
            )
            hints = ["Undo addition or subtraction before division.", "After isolating the x-term, divide both sides by the coefficient."]
            distractors = [str(x_value + 2), str(total - offset), str(coefficient)]
            correct = str(x_value)
            skill_tag = "Two-step equations"
        else:
            roots = sorted(rng.sample(range(2, 8), 2))
            b = -(roots[0] + roots[1])
            c = roots[0] * roots[1]
            prompt = f"Which solution set solves x^2 {self._signed(b)}x + {c} = 0?"
            correct = f"x = {roots[0]} or x = {roots[1]}"
            explanation = (
                f"Factor the quadratic into (x - {roots[0]})(x - {roots[1]}) = 0, "
                f"so the roots are {roots[0]} and {roots[1]}."
            )
            hints = ["Look for two numbers that multiply to the constant term.", "Those same numbers should add to the middle coefficient."]
            distractors = [
                f"x = {-roots[0]} or x = {-roots[1]}",
                f"x = {roots[0]} only",
                f"x = {roots[1]} only",
            ]
            skill_tag = "Quadratic factoring"

        return self._build_choice_question(
            prompt=prompt,
            correct=correct,
            distractors=distractors,
            explanation=explanation,
            hints=hints,
            skill_tag=skill_tag,
            question_number=question_number,
            rng=rng,
        )

    def _geometry_question(
        self,
        *,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        if difficulty == "easy":
            length = rng.randint(4, 12)
            width = rng.randint(3, 10)
            correct = 2 * (length + width)
            prompt = f"What is the perimeter of a rectangle with length {length} and width {width}?"
            explanation = f"Perimeter = 2(length + width) = 2({length} + {width}) = {correct}."
            hints = ["Add length and width first.", "Multiply that sum by 2."]
            distractors = [str(length * width), str(correct + 2), str(length + width)]
            correct_text = str(correct)
            skill_tag = "Perimeter"
        elif difficulty == "medium":
            base = rng.randint(6, 18)
            height = rng.randint(4, 12)
            correct = (base * height) // 2
            prompt = f"What is the area of a triangle with base {base} and height {height}?"
            explanation = f"Area = 1/2 x base x height = 1/2 x {base} x {height} = {correct}."
            hints = ["Multiply base by height.", "Then divide by 2."]
            distractors = [str(base * height), str(correct + height), str(correct - base // 3)]
            correct_text = str(correct)
            skill_tag = "Area of triangles"
        else:
            triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
            a, b, correct = rng.choice(triples)
            prompt = f"A right triangle has legs {a} and {b}. What is the hypotenuse?"
            explanation = f"Use the Pythagorean theorem: c^2 = {a}^2 + {b}^2 = {a*a + b*b}, so c = {correct}."
            hints = ["Square both legs and add them.", "Take the square root at the end."]
            distractors = [str(a + b), str(correct - 1), str(correct + 2)]
            correct_text = str(correct)
            skill_tag = "Pythagorean theorem"

        return self._build_choice_question(
            prompt=prompt,
            correct=correct_text,
            distractors=distractors,
            explanation=explanation,
            hints=hints,
            skill_tag=skill_tag,
            question_number=question_number,
            rng=rng,
        )

    def _statistics_question(
        self,
        *,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        if difficulty == "easy":
            values = sorted(rng.sample(range(4, 20), 5))
            total = sum(values)
            correct = total // len(values)
            prompt = f"What is the mean of {', '.join(str(value) for value in values)}?"
            explanation = f"Add the values to get {total}, then divide by 5 to get {correct}."
            hints = ["Mean means average.", "Sum all values, then divide by how many values there are."]
            distractors = [str(values[2]), str(correct + 2), str(total)]
            correct_text = str(correct)
            skill_tag = "Mean"
        elif difficulty == "medium":
            red = rng.randint(3, 7)
            blue = rng.randint(2, 6)
            total = red + blue
            prompt = f"A bag has {red} red marbles and {blue} blue marbles. What is the probability of drawing a blue marble?"
            correct_text = f"{blue}/{total}"
            explanation = f"Probability = favorable outcomes / total outcomes = {blue}/{total}."
            hints = ["Count the blue marbles.", "Probability is part over whole."]
            distractors = [f"{red}/{total}", f"{blue}/{red}", f"{total}/{blue}"]
            skill_tag = "Basic probability"
        else:
            total_students = rng.choice([20, 24, 30])
            passed = rng.randint(total_students // 2, total_students - 4)
            athletes = rng.randint(6, passed)
            prompt = (
                f"In a class of {total_students} students, {passed} passed a test and {athletes} "
                f"were athletes who passed. What is P(athlete | passed)?"
            )
            correct_text = f"{athletes}/{passed}"
            explanation = f"Conditional probability given passed means focus only on the {passed} students who passed, so the ratio is {athletes}/{passed}."
            hints = ["The condition changes the total group.", "Only look at students who passed."]
            distractors = [f"{athletes}/{total_students}", f"{passed}/{total_students}", f"{passed}/{athletes}"]
            skill_tag = "Conditional probability"

        return self._build_choice_question(
            prompt=prompt,
            correct=correct_text,
            distractors=distractors,
            explanation=explanation,
            hints=hints,
            skill_tag=skill_tag,
            question_number=question_number,
            rng=rng,
        )

    def _trigonometry_question(
        self,
        *,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        if difficulty == "easy":
            prompt = "What is sin(30 degrees)?"
            correct = "1/2"
            explanation = "From the 30-60-90 triangle, the side opposite 30 degrees is half the hypotenuse, so sin(30) = 1/2."
            hints = ["Think about the 30-60-90 special triangle.", "Sine means opposite over hypotenuse."]
            distractors = ["sqrt(3)/2", "1", "0"]
            skill_tag = "Special-angle trig"
        elif difficulty == "medium":
            opposite = rng.choice([6, 8, 9, 12])
            hypotenuse = opposite + rng.choice([6, 8, 12])
            prompt = f"In a right triangle, the opposite side is {opposite} and the hypotenuse is {hypotenuse}. What is sin(theta)?"
            correct = f"{opposite}/{hypotenuse}"
            explanation = f"Sine uses opposite over hypotenuse, so sin(theta) = {opposite}/{hypotenuse}."
            hints = ["Use SOH.", "Take opposite divided by hypotenuse."]
            distractors = [f"{hypotenuse}/{opposite}", f"{opposite}/{hypotenuse - opposite}", f"{hypotenuse - opposite}/{hypotenuse}"]
            skill_tag = "SOHCAHTOA"
        else:
            prompt = "Which identity is always true?"
            correct = "sin^2(theta) + cos^2(theta) = 1"
            explanation = "The Pythagorean identity is one of the core trig identities and holds for every angle theta."
            hints = ["Think about the unit circle.", "There is a standard identity involving sine squared and cosine squared."]
            distractors = [
                "sin(theta) + cos(theta) = 1",
                "tan(theta) = sin(theta) x cos(theta)",
                "sin(theta) = 1/cos(theta)",
            ]
            skill_tag = "Trig identities"

        return self._build_choice_question(
            prompt=prompt,
            correct=correct,
            distractors=distractors,
            explanation=explanation,
            hints=hints,
            skill_tag=skill_tag,
            question_number=question_number,
            rng=rng,
        )

    def _calculus_question(
        self,
        *,
        education_level: str,
        difficulty: str,
        rng: random.Random,
        question_number: int,
    ) -> dict[str, Any]:
        if difficulty == "easy":
            coefficient = rng.randint(2, 7)
            power = rng.randint(2, 5)
            new_coefficient = coefficient * power
            new_power = power - 1
            prompt = f"What is the derivative of {coefficient}x^{power}?"
            correct = self._format_term(new_coefficient, new_power)
            explanation = f"Use the power rule: d/dx(ax^n) = a*n*x^(n-1), so the derivative is {correct}."
            hints = ["Bring the exponent down to the front.", "Then lower the exponent by 1."]
            distractors = [
                self._format_term(coefficient + power, power - 1),
                self._format_term(new_coefficient, power),
                self._format_term(coefficient, power - 1),
            ]
            skill_tag = "Power rule"
        elif difficulty == "medium":
            a = rng.randint(2, 5)
            b = rng.randint(2, 6)
            c = rng.randint(1, 4)
            prompt = f"What is the derivative of {a}x^{b} - {c}x?"
            correct = f"{a*b}x^{b-1} - {c}"
            explanation = f"Differentiate each term separately: {a}x^{b} becomes {a*b}x^{b-1}, and -{c}x becomes -{c}."
            hints = ["Differentiate term by term.", "The derivative of kx is just k."]
            distractors = [f"{a*b}x^{b} - {c}", f"{a+b}x^{b-1} - {c}", f"{a*b}x^{b-1} - {c}x"]
            skill_tag = "Polynomial derivatives"
        else:
            inner = rng.randint(2, 5)
            prompt = f"What is the derivative of ({inner}x + 1)^2?"
            correct = f"{2 * inner}({inner}x + 1)"
            explanation = f"Use the chain rule: derivative of u^2 is 2u, then multiply by u' = {inner}, giving {2 * inner}({inner}x + 1)."
            hints = ["Start with the outer square.", "Then multiply by the derivative of the inside."]
            distractors = [f"2({inner}x + 1)", f"{inner}({inner}x + 1)^2", f"{2 * inner}x + 1"]
            skill_tag = "Chain rule"

        return self._build_choice_question(
            prompt=prompt,
            correct=correct,
            distractors=distractors,
            explanation=explanation,
            hints=hints,
            skill_tag=skill_tag,
            question_number=question_number,
            rng=rng,
        )

    def _build_choice_question(
        self,
        *,
        prompt: str,
        correct: str,
        distractors: list[str],
        explanation: str,
        hints: list[str],
        skill_tag: str,
        question_number: int,
        rng: random.Random,
    ) -> dict[str, Any]:
        options = self._shuffle_options(correct=correct, distractors=distractors, rng=rng)
        return {
            "id": f"q{question_number}",
            "prompt": prompt,
            "options": options,
            "correct_index": options.index(correct),
            "hints": hints[:2],
            "explanation": explanation,
            "skill_tag": skill_tag,
        }

    def _shuffle_options(self, *, correct: str, distractors: list[str], rng: random.Random) -> list[str]:
        options = [correct]
        for distractor in distractors:
            if distractor not in options:
                options.append(distractor)

        while len(options) < 4:
            options.append(str(int(DIFFICULTY_MULTIPLIERS["medium"] * 10) + len(options)))

        rng.shuffle(options)
        return options[:4]

    def _signed(self, value: int) -> str:
        return f"+ {value}" if value >= 0 else f"- {abs(value)}"

    def _format_term(self, coefficient: int, power: int) -> str:
        if power == 0:
            return str(coefficient)
        if power == 1:
            return f"{coefficient}x"
        return f"{coefficient}x^{power}"
