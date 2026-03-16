"""
Django management command: evaluate_search

Usage:
    python manage.py evaluate_search
    python manage.py evaluate_search --compare-to eval_2024-01-01_00-00.json
    python manage.py evaluate_search --generate-judgments
    python manage.py evaluate_search --benchmark
    python manage.py evaluate_search --generate-judgments --use-gpt
"""

import sys
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Evaluate Zarailink search quality and check regression gates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--compare-to',
            type=str,
            default=None,
            help='Previous eval results JSON filename (in evaluation/results/) for delta comparison',
        )
        parser.add_argument(
            '--generate-judgments',
            action='store_true',
            default=False,
            help='Re-generate golden judgments before evaluating',
        )
        parser.add_argument(
            '--use-gpt',
            action='store_true',
            default=False,
            help='Use GPT-4o-mini as judge (requires OPENAI_KEY env var)',
        )
        parser.add_argument(
            '--benchmark',
            action='store_true',
            default=False,
            help='Also run latency benchmark',
        )
        parser.add_argument(
            '--benchmark-queries',
            type=int,
            default=50,
            help='Number of queries for latency benchmark (default: 50)',
        )
        parser.add_argument(
            '--no-save',
            action='store_true',
            default=False,
            help='Do not save evaluation results to disk',
        )

    def handle(self, *args, **options):
        compare_to = options['compare_to']
        gen_judgments = options['generate_judgments']
        use_gpt = options['use_gpt']
        run_benchmark = options['benchmark']
        no_save = options['no_save']

        # Step 1: Generate judgments if requested
        if gen_judgments:
            self.stdout.write('Generating relevance judgments...')
            try:
                from evaluation.generate_judgments import run as gen_run
                result = gen_run(use_gpt=use_gpt if use_gpt else None)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Judgments generated: {result['total_pairs']} pairs "
                        f"(mode: {result['judge_mode']})"
                    )
                )
            except Exception as e:
                raise CommandError(f'Failed to generate judgments: {e}')

        # Step 2: Run evaluation
        self.stdout.write('Running evaluation...')
        try:
            from evaluation.evaluate import evaluate
            result = evaluate(compare_to=compare_to, save=not no_save)
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Evaluation failed: {e}')

        # Report
        metrics = result.get('metrics', {})
        self.stdout.write('\nMetrics:')
        for k, v in metrics.items():
            self.stdout.write(f'  {k}: {v:.4f}')

        # Regression gate
        if not result.get('regression_guard_passed', True):
            self.stderr.write(
                self.style.ERROR(
                    '\nREGRESSION DETECTED: NDCG@10 dropped beyond threshold. '
                    'Exiting with code 1.'
                )
            )
            sys.exit(1)

        # Targets check
        if result.get('targets_passed'):
            self.stdout.write(self.style.SUCCESS('\nAll metric targets PASSED.'))
        else:
            self.stdout.write(self.style.WARNING('\nSome metric targets not yet met (see log above).'))

        # Step 3: Benchmark if requested
        if run_benchmark:
            self.stdout.write('\nRunning latency benchmark...')
            try:
                from evaluation.benchmark_latency import run_benchmark as bench
                bench_result = bench(options['benchmark_queries'])
                p95 = bench_result['timings']['total_ms']['p95']
                if bench_result.get('p95_passed'):
                    self.stdout.write(self.style.SUCCESS(f'Latency P95: {p95:.1f}ms (PASS)'))
                else:
                    self.stdout.write(self.style.WARNING(f'Latency P95: {p95:.1f}ms (EXCEEDS 200ms target)'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Benchmark failed: {e}'))
