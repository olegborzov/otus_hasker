from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.http import (
    HttpResponseNotFound, HttpResponseBadRequest, HttpResponseNotAllowed,
    HttpResponseForbidden
)

from hasker.user.models import User
from hasker.question.models import Question, Tag, Answer


class IndexViewTests(TestCase):
    questions = {}

    def setUp(self):
        test_user = User.objects.create_user(
            username="test1",
            email="test1@mail.com",
            password="password"
        )

        self.questions["question_1"] = Question.objects.create(
            title="question_1",
            text="question_1",
            author=test_user,
            published=datetime.today() - timedelta(days=2)
        )
        self.questions["question_1"].save()
        self.questions["question_1"].vote(user=test_user)

        self.questions["question_2"] = Question.objects.create(
            title="question_2",
            text="question_2",
            author=test_user,
            published=datetime.today() - timedelta(days=1)
        )
        self.questions["question_2"].save()
        self.questions["question_2"].vote(user=test_user)

        self.questions["question_3"] = Question.objects.create(
            title="question_3",
            text="question_3",
            author=test_user,
            published=datetime.today()
        )
        self.questions["question_3"].save()

    def test_questions_sorted_by_pub_date(self):
        response = self.client.get(reverse("question:home"))

        self.assertListEqual(
            list(response.context["questions"]),
            [
                self.questions["question_3"],
                self.questions["question_2"],
                self.questions["question_1"]
            ]
        )

    def test_questions_sorted_by_rating_and_pub_date(self):
        response = self.client.get(reverse("question:hot"))

        self.assertListEqual(
            list(response.context["questions"]),
            [
                self.questions["question_2"],
                self.questions["question_1"],
                self.questions["question_3"]
            ]
        )


class SearchViewTests(TestCase):
    questions = {}

    def setUp(self):
        test_user = User.objects.create_user(
            username="test1",
            email="test1@mail.com",
            password="password"
        )

        test_tag = Tag.objects.create(name="foo")

        self.questions["question_1"] = Question.objects.create(
            title="footitle",
            text="footext",
            author=test_user,
        )
        self.questions["question_1"].tags.add(test_tag)
        self.questions["question_1"].save()

        self.questions["question_2"] = Question.objects.create(
            title="bartitle",
            text="bartext",
            author=test_user,
        )
        self.questions["question_2"].save()

    def test_search_by_empty_query(self):
        response = self.client.get(
            reverse("question:search_results"), follow=True
        )
        self.assertEqual(
            response.status_code, HttpResponseBadRequest.status_code
        )

    def test_search_by_empty_tag(self):
        response = self.client.get(
            reverse("question:search_results") + "?q=tag:", follow=True
        )
        self.assertEqual(
            response.status_code, HttpResponseBadRequest.status_code
        )

    def test_search_by_not_exist_tag(self):
        response = self.client.get(
            reverse("question:search_results") + "?q=tag:badtag", follow=True
        )
        self.assertEqual(
            response.status_code, HttpResponseNotFound.status_code
        )

    def test_search_by_phrase_empty_results(self):
        response = self.client.get(
            reverse("question:search_results") + "?q=badphrase", follow=True
        )
        self.assertEqual(
            response.status_code, 200
        )
        self.assertListEqual(
            list(response.context["questions"]),
            []
        )

    def test_search_by_title(self):
        response = self.client.get(
            reverse("question:search_results") + "?q=footitle", follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            list(response.context["questions"]),
            [self.questions["question_1"]]
        )

    def test_search_by_text(self):
        response = self.client.get(
            reverse("question:search_results") + "?q=bartext", follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            list(response.context["questions"]),
            [self.questions["question_2"]]
        )

    def test_search_by_tag(self):
        response = self.client.get(
            reverse("question:search_results") + "?q=tag:foo", follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            list(response.context["questions"]),
            [self.questions["question_1"]]
        )


class VoteViewTests(TestCase):

    def clear_likers_dislikers(self, question: Question):
        question.likers.clear()
        question.dislikers.clear()

    def setUp(self):
        self.credentials = {
            "username": "test", "password": "password"
        }
        self.credentials_2 = {
            "username": "test2", "password": "password"
        }
        self.user = User.objects.create_user(**self.credentials)
        self.user_2 = User.objects.create_user(**self.credentials_2)

        self.question = Question.objects.create(
            title="question_1",
            text="question_1",
            author=self.user_2,
            published=datetime.today() - timedelta(days=2)
        )
        self.question.save()

    def test_vote_bad_method(self):
        response = self.client.get(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.pk,
                "vote_action": "like"
            }
        )
        self.assertEqual(
            response.status_code, HttpResponseNotAllowed.status_code
        )

    def test_vote_not_ajax(self):
        response = self.client.get(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.pk,
                "vote_action": "like"
            }
        )
        self.assertEqual(
            response.status_code, HttpResponseNotAllowed.status_code
        )

    def test_unauthorized_user_cant_vote_for_question(self):
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.pk,
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(
            response.status_code, HttpResponseForbidden.status_code
        )

    def test_vote_bad_vote_type(self):
        self.client.login(**self.credentials)
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "bad",
                "vote_id": self.question.pk,
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(
            response.status_code, HttpResponseBadRequest.status_code
        )

    def test_vote_bad_vote_id(self):
        self.client.login(**self.credentials)
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": "bad vote_id",
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(
            response.status_code, HttpResponseBadRequest.status_code
        )

    def test_vote_bad_vote_action(self):
        self.client.login(**self.credentials)
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": "1",
                "vote_action": "bad"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(
            response.status_code, HttpResponseBadRequest.status_code
        )

    def test_vote_can_not_vote_own_object(self):
        self.client.login(**self.credentials_2)
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": "1",
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(
            response.status_code, HttpResponseForbidden.status_code
        )

    def test_vote_user_can_toggle(self):
        self.client.login(**self.credentials)
        self.clear_likers_dislikers(self.question)

        q_votes_start = self.question.votes

        self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.id,
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.id,
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        q_votes_end = self.question.votes

        self.assertEqual(q_votes_start, q_votes_end)

    def test_vote_user_can_like_than_dislike(self):
        self.client.login(**self.credentials)
        self.clear_likers_dislikers(self.question)

        self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.id,
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        q_votes = self.question.votes

        self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.id,
                "vote_action": "dislike"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        new_q_votes = self.question.votes

        self.assertEqual(q_votes-2, new_q_votes)

    def test_vote_good_vote_like(self):
        self.client.login(**self.credentials)
        self.clear_likers_dislikers(self.question)

        q_votes = self.question.votes
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.id,
                "vote_action": "like"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        new_q_votes = self.question.votes

        self.assertEqual(response.status_code, 200)
        self.assertEqual(q_votes+1, new_q_votes)

    def test_vote_good_vote_dislike(self):
        self.client.login(**self.credentials)
        self.clear_likers_dislikers(self.question)

        q_votes = self.question.votes
        response = self.client.post(
            reverse("question:vote"),
            data={
                "vote_type": "q",
                "vote_id": self.question.id,
                "vote_action": "dislike"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        new_q_votes = self.question.votes

        self.assertEqual(response.status_code, 200)
        self.assertEqual(q_votes-1, new_q_votes)
