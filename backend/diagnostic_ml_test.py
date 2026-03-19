import sys
import os

print('--- ML Diagnostics ---')

def test_import(module_name):
    try:
        __import__(module_name)
        print(f'[OK] {module_name} imported successfully.')
        return True
    except Exception as e:
        print(f'[FAIL] {module_name} failed: {type(e).__name__}: {e}')
        return False

print('\nBase Libraries:')
test_import('torch')
test_import('transformers')
test_import('rapidfuzz')
test_import('sentence_transformers')

print('\nGLiNER:')
if test_import('gliner'):
    try:
        from gliner import GLiNER
        print('  Attempting to load GLiNER base model... (this may take a moment if downloading)')
        model = GLiNER.from_pretrained('urchade/gliner_base')
        print('  [OK] GLiNER base model loaded.')
        out = model.predict_entities('Buy 50 tons of sugar from Brazil', labels=['product', 'country', 'quantity'])
        print(f'  [TEST] Extracted: {out}')
    except Exception as e:
        print(f'  [FAIL] GLiNER initialization failed: {type(e).__name__}: {e}')

print('\nSetFit:')
if test_import('setfit'):
    try:
        from setfit import SetFitModel
        path = r'C:\Users\Dell\Documents\ZaraiLink\backend\search\models\setfit_trade_intent'
        if os.path.exists(path):
            print(f'  Found path: {path}. Attempting to load...')
            model = SetFitModel.from_pretrained(path)
            print('  [OK] SetFit model loaded.')
            out = model.predict(['Looking to export dates to UK'])
            print(f'  [TEST] Predicted: {out}')
        else:
            print(f'  [FAIL] Model path does not exist: {path}')
    except Exception as e:
        print(f'  [FAIL] SetFit initialization failed: {type(e).__name__}: {e}')

print('\nDiagnostics Complete.')
