from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Plan, Category
from .serializers import *
from datetime import datetime, timedelta
from django.utils import timezone
from calendar import monthrange
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from users.models import Profile
from notifications.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.decorators import api_view

User = get_user_model()

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        username = self.kwargs.get('username')
        return Category.objects.filter(author__username=username) if username else Category.objects.all()

    def list(self, request, username=None):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(
            {"message": "카테고리 조회에 성공하였습니다.", "result": serializer.data},
            status=status.HTTP_200_OK
        )


    def create(self, request, username=None):
        user = get_object_or_404(Profile, username=username)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=user)
            return Response({"message": "카테고리 생성에 성공하였습니다.", "result": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": "카테고리 생성에 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def update(self, request, username=None, pk=None):
        user = get_object_or_404(User, username=username)
        category = get_object_or_404(Category, pk=pk, author=user)
        serializer = self.get_serializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "카테고리 수정에 성공했습니다.", "result": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "카테고리 수정에 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def destroy(self, request, username=None, pk=None):
        user = get_object_or_404(User, username=username)
        category = get_object_or_404(Category, pk=pk, author=user)
        category.delete()
        return Response({"message": "카테고리 삭제에 성공했습니다."}, status=status.HTTP_200_OK)
        
class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_queryset(self):
        username = self.kwargs.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            return Plan.objects.filter(author=user)
        return Plan.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"message": "일정 조회에 성공하였습니다.", "result": serializer.data},
            status=status.HTTP_200_OK
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"message": "일정 조회에 성공하였습니다.", "result": serializer.data},
            status=status.HTTP_200_OK
        )


    def create(self, request, username=None):
        # username으로 사용자 객체 찾기
        user = get_object_or_404(Profile, username=username)
        
        # category id로 카테고리 객체 찾기
        category_id = request.data.get('category')
        category = get_object_or_404(Category, id=category_id) 
        
        # participant id 리스트 가져오기
        participant_usernames = request.data.get('participant', [])
        
        # 시리얼라이저에 유효성 검사 진행
        serializer = PlanSerializer(data=request.data)
        
        if serializer.is_valid():
            # start와 end 시간을 KST로 변환
            start_time = serializer.validated_data.get('start').astimezone(timezone.get_current_timezone())
            end_time = serializer.validated_data.get('end').astimezone(timezone.get_current_timezone())

            # Plan 객체 생성
            plan = Plan.objects.create(
                author=user,
                title=serializer.validated_data.get('title'),
                category=category,
                start=start_time,
                end=end_time,
                memo=serializer.validated_data.get('memo'),
                is_completed=serializer.validated_data.get('is_completed'),
            )
            

            # participant id 모두 객체로 변환
            participants = Profile.objects.filter(username__in=participant_usernames)
            plan.participant.set(participants)  # manyToMany 필드는 이렇게 set으로 처리 해줘야 합니다 !
            
            response_serializer = PlanSerializer(plan)
            return Response({"message": "일정 생성에 성공했습니다.", "result": response_serializer.data}, status=status.HTTP_201_CREATED)
                
        return Response({"message": "일정 생성에 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, username=None, pk=None):
        # username으로 사용자 객체 찾기
        user = get_object_or_404(Profile, username=username)
        
        # 해당하는 Plan 객체 찾기
        plan = get_object_or_404(Plan, pk=pk, author=user)

        # category id로 카테고리 객체 찾기 (선택적)
        category_id = request.data.get('category')
        category = get_object_or_404(Category, id=category_id)

        # participant id 리스트 가져오기
        participant_usernames = request.data.get('participant', [])
        
        # 시리얼라이저에 유효성 검사 진행
        serializer = PlanSerializer(plan, data=request.data, partial=True)  # partial=True는 부분 업데이트 !

        if serializer.is_valid():
            # start와 end 시간을 KST로 변환 (필요 시)
            start_time = serializer.validated_data.get('start').astimezone(timezone.get_current_timezone()) if 'start' in serializer.validated_data else plan.start.astimezone(timezone.get_current_timezone())
            end_time = serializer.validated_data.get('end').astimezone(timezone.get_current_timezone()) if 'end' in serializer.validated_data else plan.end.astimezone(timezone.get_current_timezone())

            # Plan 객체 업데이트
            updated_plan = serializer.save(
                category=category,  # 카테고리 업데이트
            )
            

            # participant id 모두 객체로 변환
            participants = Profile.objects.filter(username__in=participant_usernames)
            updated_plan.participant.set(participants)  # manyToMany 필드는 이렇게 set으로 처리 해줘야 합니다 !

            response_serializer = PlanSerializer(updated_plan)
            return Response({"message": "일정 수정에 성공했습니다.", "result": response_serializer.data}, status=status.HTTP_200_OK)
                
        return Response({"message": "일정 수정에 실패했습니다.", "result": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, username=None, pk=None):
        user = get_object_or_404(User, username=username)
        plan = get_object_or_404(Plan, pk=pk, author=user)
        plan.delete()
        return Response({"message": "일정 삭제에 성공했습니다."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def monthly(self, request, username=None):
        user = get_object_or_404(User, username=username)
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))

        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())  # KST로 변환
        end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.get_current_timezone())  # KST로 변환

        plans = self.get_queryset().filter(
            author=user,
            start__gte = start_date,
            start__lte = end_date
        ).order_by('start')

        calendar_data = {}
        
        for day in range(1, last_day+1):
            date_key = datetime(year,month,day).date().isoformat()
            calendar_data[date_key] = {
                'displayed_plans': [],
                'remaining_count': 0
            }

        plan_counts = {}
        for plan in plans:
            date_key = plan.start.astimezone(timezone.get_current_timezone()).date().isoformat()  # KST로 변환
            plan_counts[date_key] = plan_counts.get(date_key, 0) + 1

            # 시리얼라이저로 반환
            plan_data = PlanSerializer(plan).data 

            if len(calendar_data[date_key]['displayed_plans']) < 2:
                calendar_data[date_key]['displayed_plans'].append(plan_data)
            else:
                calendar_data[date_key]['remaining_count'] += 1
        
        return Response({"message": "월간 캘린더 조회에 성공했습니다.", "result": calendar_data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def weekly(self, request, username=None):
        user = get_object_or_404(User, username=username)
        date_str = request.query_params.get('date')
        if date_str:
            try:
                current_date = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=0, minute=0)
            except ValueError:
                return Response({"error":"YYYY-MM-DD로 입력하세요."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            current_date = timezone.now().date()

        # 현재 날짜를 한국 시간으로 변환
        current_date = current_date.astimezone(timezone.get_current_timezone())

        # 월요일로 주 시작일 계산 (current_date.weekday()는 월요일이 0)
        start_of_week = current_date - timedelta(days=current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        plans = self.get_queryset().filter(
            author=user,
            start__date__gte=start_of_week,
            start__date__lte=end_of_week + timedelta(days=1)
        ).order_by('start')

        weekly_data = {}
        for i in range(7):
            date = start_of_week + timedelta(days=i)
            date_key = date.date().isoformat()
            weekly_data[date_key] = {
                'displayed_plans': [],
                'remaining_count': 0
            }
        
        for plan in plans:
            # UTC -> KST
            start_hour = plan.start.astimezone(timezone.get_current_timezone())
            end_hour = plan.end.astimezone(timezone.get_current_timezone()) if plan.end else start_hour
            
            date_key = start_hour.date().isoformat()

            # 시리얼라이저로 반환
            plan_data = PlanSerializer(plan).data 

            if len(weekly_data[date_key]['displayed_plans']) < 2:
                weekly_data[date_key]['displayed_plans'].append(plan_data)
            else:
                weekly_data[date_key]['remaining_count'] += 1
                
        return Response({"message": "주간 캘린더 조회에 성공했습니다.", "result": weekly_data}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'])
    def daily(self, request, username=None):
        user = get_object_or_404(User, username=username)
        date_str = request.query_params.get('date')
        if date_str:
            try:
                current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "YYYY-MM-DD로 입력하세요."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            current_date = timezone.now().date()

        # 24시간 동안 10분 간격의 타임 슬롯 생성
        time_slots = {f"{hour:02d}:{minute:02d}" : [] for hour in range(24) for minute in range(0,60,10)}   # 0시 ~ 23시
        categories = {}

        plans = self.get_queryset().filter(author=user).order_by('start')

        for plan in plans:
            start_hour = plan.start.astimezone(timezone.get_current_timezone())  # 로컬 시간대로 변환
            end_hour = plan.end.astimezone(timezone.get_current_timezone()) if plan.end else start_hour

            # 시리얼라이저로 반환
            plan_data = PlanSerializer(plan).data 

            # 시작일과 종료일이 다를 경우 처리
            current_slot = start_hour.replace(minute=start_hour.minute // 10 * 10, second=0, microsecond=0)

            # 현재 날짜가 일정의 시작일인 경우
            if current_date == start_hour.date():
                while current_slot <= end_hour and current_slot.date() == current_date:
                    slot_key = current_slot.strftime("%H:%M")
                    if slot_key in time_slots:
                        time_slots[slot_key].append(plan_data)
                    current_slot += timedelta(minutes=10)

            # 현재 날짜가 일정의 종료일인 경우
            elif current_date == end_hour.date():
                current_slot = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
                while current_slot <= end_hour:
                    slot_key = current_slot.strftime("%H:%M")
                    if slot_key in time_slots:
                        time_slots[slot_key].append(plan_data)
                    current_slot += timedelta(minutes=10)

            # 현재 날짜가 일정의 중간 날짜인 경우(시작일과 종료일 사이)
            elif start_hour.date() < current_date < end_hour.date():
                current_slot = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
                end_of_day = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))
                while current_slot <= end_of_day:
                    slot_key = current_slot.strftime("%H:%M")
                    if slot_key in time_slots:
                        time_slots[slot_key].append(plan_data)
                    current_slot += timedelta(minutes=10)

            category_title = plan.category.title if plan.category else "Uncategorized"
            if category_title not in categories:
                categories[category_title] = []
            categories[category_title].append(plan_data)

        return Response({
            "message": "일간 캘린더 조회에 성공했습니다.",
            "result": {
                "time_slots": time_slots,
            "categories": categories
            }},
            status=status.HTTP_200_OK)

    def plan_deadline(self, plan):
        now = timezone.now().astimezone(timezone.get_current_timezone())
        plan_end = plan.end.astimezone(timezone.get_current_timezone())
        deadline = plan_end - now

        if deadline > timezone.timedelta(0) and deadline <= timezone.timedelta(hours=1) and not plan.is_completed:
            Notification.objects.create(
                recipient=plan.author,
                message=f"{plan.title} 마감시간까지 1시간 남았습니다! 잊지 말고 계획을 실행해주세요!",
                notification_type='plan_deadline'
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{plan.author.id}",
                {
                    'type': 'send_notification',
                    'message': f"{plan.title} 마감시간까지 1시간 남았습니다! 잊지 말고 계획을 실행해주세요!",
                }
            )

    def daily_achievement(self, request):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        total_plans = Plan.objects.filter(author=user, start__date=yesterday).count()
        completed_plans = Plan.objects.filter(author=user, start__date=yesterday, is_completed=True).count()
        
        Notification.objects.create(
            recipient=user,
            message=f"어제는 {total_plans}개의 계획 중에서 {completed_plans}개의 계획을 달성하셨습니다! \n {yesterday.year}년 {yesterday.month}월 {yesterday.day}일의 {user.nickname}님은 성실하셨네요!",
            notification_type='daily_achievement'
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                'type': 'send_notification',
                'message': message,
            }
        )
        
        return Response({"message": "일일 달성 알림을 생성했습니다."}, status=status.HTTP_200_OK)