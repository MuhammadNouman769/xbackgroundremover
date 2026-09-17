from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadImageForm
from .models import ProcessedImage
from .utils import process_image


def home(request):
    """
    Main landing page — upload form + hero copy, same job as
    removal.ai's "Upload an image to remove the background" screen.
    Works for guests; if logged in, the job is saved to their history.
    """
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            if request.user.is_authenticated:
                job.user = request.user
            job.save()

            success, result_bytes, error = process_image(
                original_file=job.original_image,
                background_type=job.background_type,
                background_color=job.background_color,
                background_image=job.background_image if job.background_image else None,
            )

            if success:
                job.processed_image.save(
                    f'result_{job.pk}.png', ContentFile(result_bytes), save=False
                )
                job.is_successful = True
                job.save()
                messages.success(request, 'Background removed successfully!')
                return redirect('remover:result', pk=job.pk)
            else:
                job.error_message = (
                    "We couldn't identify the foreground of your image. "
                    "Please try a clearer JPG or PNG photo."
                )
                job.save()
                messages.error(request, job.error_message)
                return redirect('remover:result', pk=job.pk)
    else:
        form = UploadImageForm()

    recent_examples = ProcessedImage.objects.filter(is_successful=True)[:4]
    return render(request, 'remover/home.html', {
        'form': form,
        'recent_examples': recent_examples,
    })


def result(request, pk):
    job = get_object_or_404(ProcessedImage, pk=pk)
    # Guests may only view their own just-created job in this session-less
    # simple version; logged-in users may only view their own jobs.
    if request.user.is_authenticated and job.user_id and job.user_id != request.user.id:
        raise Http404
    return render(request, 'remover/result.html', {'job': job})


@login_required
def history(request):
    jobs = ProcessedImage.objects.filter(user=request.user)
    return render(request, 'remover/history.html', {'jobs': jobs})


def download(request, pk):
    job = get_object_or_404(ProcessedImage, pk=pk, is_successful=True)
    if not job.processed_image:
        raise Http404
    return FileResponse(
        job.processed_image.open('rb'),
        as_attachment=True,
        filename=f'xbg-remove-{job.pk}.png',
    )
