from rest_framework.decorators import api_view, permission_classes,parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DatabaseError
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from .models import Task
import openpyxl
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (TaskSerializer,ForgotPasswordSerializer,ResetPasswordSerializer)
from datetime import datetime

#! For get and post 

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def task_list_create(request):
    try:
        if request.method == "GET":
            tasks = Task.objects.filter(assigned_to=request.user)
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(assigned_to=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except DatabaseError as e:
        return Response({"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#! for get,put,patch,delete by their respective id's

@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk, assigned_to=request.user)
    except ObjectDoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return Response({"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        
        if request.method == "GET":
            serializer = TaskSerializer(task)
            return Response(serializer.data)

       
        elif request.method == "PUT":
            serializer = TaskSerializer(task, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

 
        elif request.method == "PATCH":
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

       
        elif request.method == "DELETE":
            task.delete()
            return Response({"message": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    except ValidationError as e:
        return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#! Forgot password and reset password by using uid and token 

token_generator = PasswordResetTokenGenerator()
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"http://localhost:8000/reset-password/{uid}/{token}/"

            send_mail(
                subject="Password Reset Request",
                message=f"uid and token in the  below link to reset your password:\n\n{reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response({
                "message": "If the email exists, a reset link has been sent.",
                
            })
        except User.DoesNotExist:
            return Response({"message": "If the email exists, a reset link has been sent."})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if not token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

            
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successful"})

        except User.DoesNotExist:
            return Response({"error": "Invalid user"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#! Uploading database

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_tasks_excel(request):
    file = request.FILES.get("file")

    if not file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    tasks_to_create = []
    skipped_rows = []

    try:
        wb = openpyxl.load_workbook(file)
        sheet = wb.active

        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            
            try:
                title, description, completed, assigned_to_id, scheduled_date = row
                
            except ValueError:
                skipped_rows.append({"row": idx, "reason": "Invalid number of columns"})
                continue

            if not title:
                skipped_rows.append({"row": idx, "reason": "Missing title"})
                continue

            if not description:
                skipped_rows.append({"row": idx, "reason": "Missing description"})
                continue

            
            try:
                user = User.objects.get(id=int(assigned_to_id))
            except (User.DoesNotExist, ValueError, TypeError):
                skipped_rows.append({"row": idx, "reason": f"Invalid user ID {assigned_to_id}"})
                continue

          
            try:
                if isinstance(scheduled_date, str):
                    scheduled_date = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
                elif isinstance(scheduled_date, datetime):
                    scheduled_date = scheduled_date.date()
            except Exception:
                skipped_rows.append({"row": idx, "reason": f"Invalid date format: {scheduled_date}"})
                continue

          
            if Task.objects.filter(title=title, assigned_to=user, scheduled_date=scheduled_date).exists():
                skipped_rows.append({"row": idx, "reason": f"Duplicate task '{title}' already assigned on {scheduled_date}"})
                continue

            tasks_to_create.append(Task(
                title=title,
                description=description,
                completed=bool(completed),
                assigned_to=user,
                scheduled_date=scheduled_date
            ))

      
        if tasks_to_create:
            Task.objects.bulk_create(tasks_to_create)
            created_count = len(tasks_to_create)
        else:
            created_count = 0

       
        status_code = status.HTTP_201_CREATED if created_count > 0 else status.HTTP_200_OK
        message = (
            f"{created_count} tasks uploaded successfully"
            if created_count > 0
            else "No new tasks were uploaded (all duplicates/skipped)."
        )

        return Response({
            "message": message,
            "skipped_rows": skipped_rows
        }, status=status_code)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


