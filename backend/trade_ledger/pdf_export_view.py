import subprocess
import tempfile
import os
import json
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def export_comparison_pdf(request):
    """
    Export company comparison as high-fidelity PDF using Puppeteer
    """
    try:
        data = json.loads(request.body)
        companies = data.get('companies', [])
        comparison_data = data.get('comparison_data', {})
        
        if len(companies) < 2:
            return JsonResponse({'error': 'At least 2 companies required'}, status=400)
        
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generate_comparison_pdf.js')
        
        
        node_input = json.dumps({
            'companies': companies,
            'comparisonData': comparison_data,
            'outputPath': pdf_path
        })
        
        
        result = subprocess.run(
            ['node', '-e', f"""
const {{  generateComparisonPDF }}  = require('{script_path.replace(os.sep, '/')}');
const data = {node_input};
generateComparisonPDF(data.companies, data.comparisonData, data.outputPath)
    .then(() => process.exit(0))
    .catch((err) => {{  console.error(err); process.exit(1); }} );
            """],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"PDF generation error: {result.stderr}")
            return JsonResponse({'error': 'PDF generation failed'}, status=500)
        
        
        if os.path.exists(pdf_path):
            response = FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="company-comparison-{companies[0][:20]}.pdf"'
            
            
            def cleanup():
                try:
                    os.unlink(pdf_path)
                except:
                    pass
            response.close = cleanup
            
            return response
        else:
            return JsonResponse({'error': 'PDF file not created'}, status=500)
            
    except Exception as e:
        print(f"PDF export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
