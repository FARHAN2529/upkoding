from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string

from account.models import UserSetting
from .models import UserProjectEvent, UserProjectParticipant

FROM = settings.DEFAULT_EMAIL_FROM


class UserProjectEventNotification:
    def __init__(self, event: UserProjectEvent):

        self.__user_project = event.user_project
        self.__event_user = event.user
        self.__context = {
            'domain': settings.SITE_DOMAIN,
            'user': self.__event_user,
            'user_project': self.__user_project,
            'project': self.__user_project.project,
        }
        if event.istype(UserProjectEvent.TYPE_REVIEW_REQUEST):
            self.__notify_review_request()
        if event.istype(UserProjectEvent.TYPE_REVIEW_MESSAGE):
            self.__notify_project_message()
        if event.istype(UserProjectEvent.TYPE_PROJECT_COMPLETE):
            self.__notify_project_approved()
        if event.istype(UserProjectEvent.TYPE_PROJECT_INCOMPLETE):
            self.__notify_project_disapproved()

    def __notify_review_request(self):
        """
        Send email to staff/project creator about project need a review.
        """
        tpl = 'projects/emails/project_review_request.html'

        # get all participants on this project, except the event creator.
        participants = UserProjectParticipant.objects. \
            filter(user_project=self.__user_project, subscribed=True). \
            exclude(user=self.__event_user)

        emails = []
        for p in participants:
            to_user = p.user
            # check user notification settings
            if UserSetting.objects.email_notify_project_review_request(to_user):
                self.__context.update({'to_user': to_user})
                msg = render_to_string(tpl, self.__context)
                subject = f'[Proyek] Permintaan review dari @{self.__event_user.username}'
                emails.append((subject, msg, FROM, [to_user.email]))
        if emails:
            send_mass_mail(emails, fail_silently=True)

    def __notify_project_message(self):
        """
        Send email to participants about new message in project.
        """
        tpl = 'projects/emails/project_message.html'

        # get all participants on this project, except the event creator.
        participants = UserProjectParticipant.objects. \
            filter(user_project=self.__user_project, subscribed=True). \
            exclude(user=self.__event_user)

        emails = []
        for p in participants:
            to_user = p.user
            # check user notification settings
            if UserSetting.objects.email_notify_project_message(to_user):
                self.__context.update({'to_user': to_user})
                msg = render_to_string(tpl, self.__context)
                subject = f'[Proyek] Pesan dari @{self.__event_user.username}'
                emails.append((subject, msg, FROM, [to_user.email]))
        if emails:
            send_mass_mail(emails, fail_silently=True)

    def __notify_project_approved(self):
        """
        Send email to user who working on a project about their project has been approved.
        """
        tpl = 'projects/emails/project_approved.html'
        user_project_owner = self.__user_project.user

        # check user notification settings
        if UserSetting.objects.email_notify_project_approved(user_project_owner):
            self.__context.update({'to_user': user_project_owner})
            msg = render_to_string(tpl, self.__context)
            subject = '[Proyek] Proyek kamu telah disetujui!'
            send_mail(subject, msg, FROM, [user_project_owner.email], fail_silently=True)

    def __notify_project_disapproved(self):
        """
        Send email to user who working on a project about their project status changed.
        """
        tpl = 'projects/emails/project_disapproved.html'
        user_project_owner = self.__user_project.user

        # check user notification settings
        if UserSetting.objects.email_notify_project_disapproved(user_project_owner):
            self.__context.update({'to_user': user_project_owner})
            msg = render_to_string(tpl, self.__context)
            subject = '[Proyek] Status proyek kamu diralat'
            send_mail(subject, msg, FROM, [user_project_owner.email], fail_silently=True)
