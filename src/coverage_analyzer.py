import os
import subprocess
from pathlib import Path
from typing import Dict, List

import coverage


class CoverageAnalyzer:
    def __init__(self, source_dir: str = "source_files"):
        self.source_dir = source_dir
        self.coverage_data_file = ".coverage"
        self.html_report_dir = "coverage_html_report"

    def run_tests_with_coverage(self, test_file_path: str, source_file_path: str) -> Dict:
        """Run tests with coverage analysis."""
        try:
            # Get the relative path of the source file within the source directory
            source_file_name = os.path.basename(source_file_path)

            # Get the module name (without .py extension)
            module_name = os.path.splitext(source_file_name)[0]

            # Get the module path in dot notation (for coverage source)
            if os.path.dirname(source_file_path) == self.source_dir or source_file_path.startswith(f"{self.source_dir}/"):
                module_path = f"source_files.{module_name}"
            else:
                module_path = module_name

            # Initialize coverage with specific source file
            cov = coverage.Coverage(
                source=[module_path],  # Use module notation instead of file path
                data_file=self.coverage_data_file,
                config_file=".coveragerc"
            )

            # Start coverage collection
            cov.start()

            # Set up environment with PYTHONPATH to include project root
            env = os.environ.copy()
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root

            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                test_file_path,
                f"--cov={module_path}",  # Use module notation instead of file path
                "--cov-report=term-missing",
                "-v"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                env=env
            )

            # Stop coverage collection
            cov.stop()
            cov.save()

            # Generate coverage report
            coverage_report = self._generate_coverage_report(cov, source_file_path)

            # Format coverage report as string
            coverage_str = self._format_coverage_report_as_string(coverage_report)

            return {
                "success": result.returncode == 0,
                "test_output": result.stdout,
                "coverage_report": coverage_report,
                "coverage_percentage": coverage_report.get("total_coverage", 0),
                "coverage_str": coverage_str
            }

        except Exception as e:
            error_message = str(e)
            return {
                "success": False,
                "error": error_message,
                "coverage_report": None,
                "coverage_percentage": 0,
                "coverage_str": f"Error running tests with coverage: {error_message}"
            }

    def _generate_coverage_report(self, cov: coverage.Coverage, source_file: str) -> Dict:
        """Generate detailed coverage report."""
        try:
            # Get coverage data
            coverage_data = cov.get_data()

            # Analyze specific file
            file_path = Path(source_file)

            # Get line coverage
            analysis = cov.analysis2(str(file_path))
            # Handle the case where analysis2 returns more than 4 values
            filename, executed_lines, missing_lines, excluded_lines = analysis[:4]

            # Calculate coverage percentage
            total_lines = len(executed_lines) + len(missing_lines)
            if total_lines > 0:
                coverage_percentage = (len(executed_lines) / total_lines) * 100
            else:
                coverage_percentage = 0

            # Get function coverage
            function_coverage = self._analyze_function_coverage(
                str(file_path), executed_lines, missing_lines
            )

            return {
                "filename": filename,
                "total_coverage": round(coverage_percentage, 2),
                "executed_lines": list(executed_lines),
                "missing_lines": list(missing_lines),
                "excluded_lines": list(excluded_lines),
                "total_lines": total_lines,
                "covered_lines": len(executed_lines),
                "function_coverage": function_coverage
            }

        except Exception as e:
            return {"error": str(e)}

    def _analyze_function_coverage(self, file_path: str, executed_lines: set, missing_lines: set) -> List[Dict]:
        """Analyze coverage at function level."""
        try:
            import ast

            with open(file_path, 'r') as f:
                source_code = f.read()

            tree = ast.parse(source_code)
            function_coverage = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_start = node.lineno
                    func_end = node.end_lineno or func_start

                    func_lines = set(range(func_start, func_end + 1))
                    covered_func_lines = func_lines.intersection(executed_lines)
                    total_func_lines = len(func_lines)

                    if total_func_lines > 0:
                        func_coverage_pct = (len(covered_func_lines) / total_func_lines) * 100
                    else:
                        func_coverage_pct = 0

                    function_coverage.append({
                        "name": node.name,
                        "start_line": func_start,
                        "end_line": func_end,
                        "coverage_percentage": round(func_coverage_pct, 2),
                        "covered_lines": len(covered_func_lines),
                        "total_lines": total_func_lines,
                        "missing_lines": list(func_lines.intersection(missing_lines))
                    })

            return function_coverage

        except Exception as e:
            return [{"error": str(e)}]

    def _format_coverage_report_as_string(self, coverage_report: Dict) -> str:
        """Format coverage report as a readable string."""
        if not coverage_report or "error" in coverage_report:
            return "Error generating coverage report"

        lines = []
        lines.append(f"Coverage Report for: {coverage_report.get('filename', 'Unknown file')}")
        lines.append(f"Total Coverage: {coverage_report.get('total_coverage', 0)}%")
        lines.append(f"Lines Covered: {coverage_report.get('covered_lines', 0)}/{coverage_report.get('total_lines', 0)}")

        # Add missing lines information
        missing_lines = coverage_report.get('missing_lines', [])
        if missing_lines:
            lines.append("\nMissing Lines:")
            # Group consecutive missing lines for better readability
            groups = []
            current_group = []

            for line in sorted(missing_lines):
                if not current_group or line == current_group[-1] + 1:
                    current_group.append(line)
                else:
                    groups.append(current_group)
                    current_group = [line]

            if current_group:
                groups.append(current_group)

            for group in groups:
                if len(group) == 1:
                    lines.append(f"  Line {group[0]}")
                else:
                    lines.append(f"  Lines {group[0]}-{group[-1]}")

        # Add function coverage information
        function_coverage = coverage_report.get('function_coverage', [])
        if function_coverage:
            lines.append("\nFunction Coverage:")
            for func in function_coverage:
                lines.append(f"  {func.get('name', 'Unknown')}: {func.get('coverage_percentage', 0)}% " +
                           f"({func.get('covered_lines', 0)}/{func.get('total_lines', 0)} lines)")

                func_missing = func.get('missing_lines', [])
                if func_missing:
                    lines.append(f"    Missing lines: {', '.join(map(str, sorted(func_missing)))}")

        return "\n".join(lines)

    def generate_coverage_summary(self, coverage_results: List[Dict]) -> Dict:
        """Generate overall coverage summary for multiple files."""
        if not coverage_results:
            return {"total_coverage": 0, "files_analyzed": 0}

        total_lines = sum(result.get("total_lines", 0) for result in coverage_results)
        total_covered = sum(result.get("covered_lines", 0) for result in coverage_results)

        overall_coverage = (total_covered / total_lines * 100) if total_lines > 0 else 0

        return {
            "total_coverage": round(overall_coverage, 2),
            "files_analyzed": len(coverage_results),
            "total_lines": total_lines,
            "covered_lines": total_covered,
            "files": coverage_results
        }
