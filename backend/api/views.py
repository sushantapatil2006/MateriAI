"""
API views for MateriAI.

Endpoints:
  POST /api/upload/  — file upload (PDF or TXT)
  POST /api/paste/   — raw text input
  POST /api/grade/<id>/ — grade the quiz
"""
import os
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FileUploadSerializer, TextInputSerializer
from .services.pdf_parser import extract_text_from_pdf, extract_text_from_txt
from .services.text_processor import clean_text, chunk_text
from .services.ai_service import process_text
from .models import StudyMaterial, Question

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared processing pipeline
# ---------------------------------------------------------------------------
def _process_text_pipeline(raw_text: str) -> dict:
    """
    Common pipeline shared by both endpoints.

    1. Clean the text
    2. Chunk it (~1500 words per chunk)
    3. Run the map-reduce AI pipeline
    4. Save to Database
    5. Return structured result without answers

    Args:
        raw_text: The raw extracted/pasted text.

    Returns:
        Dict with keys: material_id, summary, explanation, quiz.
    """
    cleaned = clean_text(raw_text)

    if not cleaned:
        raise ValueError("After cleaning, no usable text remained.")

    chunks = chunk_text(cleaned, chunk_size=1500)

    if not chunks:
        raise ValueError("Text could not be split into chunks.")

    # Get JSON from Groq
    ai_result = process_text(chunks)
    
    # Save the output to the DB securely
    material = StudyMaterial.objects.create(
        summary=ai_result.get("summary", ""),
        explanation=ai_result.get("explanation", "")
    )
    
    frontend_quiz = []
    
    # Parse generated quiz
    raw_quiz = ai_result.get("quiz", [])
    for idx, q_data in enumerate(raw_quiz):
        q = Question.objects.create(
            material=material,
            question_text=q_data.get("question", ""),
            options=q_data.get("options", []),
            correct_answer=q_data.get("answer", ""),
            order=idx
        )
        # Create a payload for the frontend WITHOUT the correct answer
        frontend_quiz.append({
            "id": q.id,
            "question": q.question_text,
            "options": q.options
        })

    return {
        "material_id": material.id,
        "summary": material.summary,
        "explanation": material.explanation,
        "quiz": frontend_quiz
    }


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------
class UploadView(APIView):
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_file = serializer.validated_data["file"]
        ext = os.path.splitext(uploaded_file.name)[1].lower()

        try:
            if ext == ".pdf":
                raw_text = extract_text_from_pdf(uploaded_file)
            elif ext == ".txt":
                raw_text = extract_text_from_txt(uploaded_file)
            else:
                return Response(
                    {"error": f"Unsupported file type: {ext}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = _process_text_pipeline(raw_text)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RuntimeError as exc:
            logger.error("AI processing error (upload): %s", exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            logger.exception("Unexpected error in upload endpoint.")
            return Response(
                {"error": "An unexpected error occurred. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# Paste endpoint
# ---------------------------------------------------------------------------
class PasteView(APIView):
    def post(self, request):
        serializer = TextInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_text = serializer.validated_data["text"]

        try:
            result = _process_text_pipeline(raw_text)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except RuntimeError as exc:
            logger.error("AI processing error (paste): %s", exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            logger.exception("Unexpected error in paste endpoint.")
            return Response(
                {"error": "An unexpected error occurred. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# ---------------------------------------------------------------------------
# Grade Quiz endpoint
# ---------------------------------------------------------------------------
class GradeQuizView(APIView):
    def post(self, request, material_id):
        user_answers = request.data.get("answers", {})
        
        try:
            material = StudyMaterial.objects.get(id=material_id)
        except StudyMaterial.DoesNotExist:
            return Response(
                {"error": "Study material not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        questions = material.questions.all()
        results = {}
        score = 0
        total = questions.count()
        
        for q in questions:
            user_ans = user_answers.get(str(q.id))
            correct = (user_ans == q.correct_answer)
            if correct:
                score += 1
                
            results[str(q.id)] = {
                "correct": correct,
                "user_answer": user_ans,
                "correct_answer": q.correct_answer
            }
            
        return Response({
            "score": score,
            "total": total,
            "results": results
        }, status=status.HTTP_200_OK)
