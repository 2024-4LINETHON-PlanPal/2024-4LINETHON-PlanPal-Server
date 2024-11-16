from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from promise.models import Promise, PromiseOption
from users.models import Profile
from notifications.models import Notification

from promise.serializers import PromiseSerializer

# 투표 상태로 전환하기
class VotingChageStatusView(APIView):
    def put(self, request, username, promise_id, format=None):
        try:
            user = Profile.objects.get(username=username)
        except Profile.DoesNotExist:
            return Response({"message": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            promise = Promise.objects.get(id=promise_id)
        except Promise.DoesNotExist:
            return Response({"message": "해당 약속을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        if not promise.user == user:
            return Response({"message": "해당 약속의 주최자가 아닙니다."}, status=status.HTTP_400_BAD_REQUEST)

        # status 변경
        promise.status = "voting"
        promise.save()

        # 참여자들에게 알림 전송
        recipients_objects = promise.members.all()
        recipients = Profile.objects.filter(username__in=recipients_objects.values('username'))

        content_type = ContentType.objects.get_for_model(promise)
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                message=f"{promise.title} 약속 투표를 진행해주세요.",
                notification_type='vote',
                content_type=content_type,
                object_id=promise.id,
                author=promise.user
            )

        serializer = PromiseSerializer(promise)

        return Response({"message": "투표하기 상태 변경에 성공하였습니다.",  "result": serializer.data}, status=status.HTTP_200_OK)



# 투표하기
class VotingView(APIView):
    def put(self, request, username, promise_id, promise_option_id, format=None):
        # 객체 찾기
        try:
            user = Profile.objects.get(username=username)
        except Profile.DoesNotExist:
            return Response({"message": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            promise = Promise.objects.get(id=promise_id)
        except Promise.DoesNotExist:
            return Response({"message": "해당 약속을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            promise_option = PromiseOption.objects.get(id=promise_option_id)
        except PromiseOption.DoesNotExist:
            return Response({"message": "해당 약속 후보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
                
        if not (promise.members.filter(id=user.id).exists() or promise.user == user):
            return Response({"message": "해당 약속의 참여자가 아닙니다."}, status=status.HTTP_400_BAD_REQUEST)

        for option in promise.promise_options.all():
            if option.vote_members.filter(id=user.id).exists():
                return Response({"message": "이미 투표했습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 투표하면 vote_members에 추가
        promise_option.vote_members.add(user)
        promise.save()

        # 모든 사용자가 투표한 경우
        if isAllVote(promise):
            promise.status = "confirming"
            final_option = voteResult(promise)
            promise.promise_options.set([final_option]) # 선정된 option으로 변경

            promise.save()

        serializer = PromiseSerializer(promise)

        return Response({"message": "투표에 성공하였습니다.",  "result": serializer.data}, status=status.HTTP_200_OK)
    

# 모든 사용자가 투표를 완료했는지 확인하는 함수
def isAllVote(promise):
    count = sum(option.vote_members.count() for option in promise.promise_options.all())
    if count >= promise.members.count() + 1:
        # 참여자들에게 알림 전송
        recipients_objects = promise.members.all()
        recipients = Profile.objects.filter(username__in=recipients_objects.values('username'))

        content_type = ContentType.objects.get_for_model(promise)
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                message=f"{promise.title} 약속을 확정해주세요.",
                notification_type='promise_accept',
                content_type=content_type,
                object_id=promise.id,
                author=promise.user
            )
        return True
    return False


# 투표 결과를 반환하는 함수
def voteResult(promise):
    option_votes = []

    # promise의 모든 옵션을 순회하면서 리스트에 저장
    for option in promise.promise_options.all():
        vote_count = option.vote_members.count()
        option_votes.append((option, vote_count))

    # 만약 아무도 투표 안 한 경우
    if not option_votes:
        return findBestOption(promise.promise_options.all())
    else :
        # 투표 수 기준으로 정렬
        option_votes.sort(key=lambda x: x[1], reverse=True)
        
        # 가장 많은 투표를 받은 옵션을 가져옴
        max_votes = option_votes[0][1]
        winning_options = [option for option, count in option_votes if count == max_votes]

        return findBestOption(winning_options)


# members_can_attend가 가장 많은 -> start가 가장 이른 option을 리턴하는 함수
def findBestOption(options):
    # 동률일 경우 members_can_attend가 가장 많은 옵션을 찾음
    if len(options) > 1:
        # members_can_attend 수 기준으로 정렬
        options.sort(key=lambda x: x.members_can_attend.count(), reverse=True)
        
        # members_can_attend도 동률인지 검사
        max_attendees = options[0].members_can_attend.count()
        final_options = [option for option in options if option.members_can_attend.count() == max_attendees]

        # members_can_attend도 동률인 경우 start 시간 기준으로 정렬
        if len(final_options) > 1:
            final_options.sort(key=lambda x: x.start)

        return final_options[0]  # 가장 이른 start 시간을 가진 옵션 리턴

    return options[0]  # 동률이 아니고 한번에 결정된 옵션 리턴

# 24시간이 지났는지 확인하는 함수
def is24HoursAfter():
    promises = Promise.objects.filter(
        status="voting",
        # created_at__lte=timezone.now() - timezone.timedelta(minutes=1)
        created_at__lte=timezone.now() - timezone.timedelta(hours=24)
    )
    
    with transaction.atomic():  # 트랜잭션 시작
        for promise in promises:
            promise.refresh_from_db()  # DB에서 최신 데이터로 갱신
            promise.status = "confirming"
            final_option = voteResult(promise)
            promise.promise_options.set([final_option])

            # 참여자들에게 알림 전송
            recipients_objects = promise.members.all()
            recipients = Profile.objects.filter(username__in=recipients_objects.values('username'))

            content_type = ContentType.objects.get_for_model(promise)
            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient,
                    message=f"{promise.title} 약속을 확정해주세요.",
                    notification_type='promise_accept',
                    content_type=content_type,
                    object_id=promise.id,
                    author=promise.user
                )

            promise.save()  