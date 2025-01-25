import argparse
from pathlib import Path
import yaml
from .ai import WorksheetGenerator

def load_config(config_path: Path):
    """Load YAML configuration file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='WorksheetAI Configuration Generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--subject', required=True, help='Subject area (e.g. coding)')
    parser.add_argument('--language', required=True, help='Programming language (e.g. python)')
    parser.add_argument('--topics', required=True, help='Comma-separated list of topics')
    parser.add_argument('--question-types', required=True, help='Comma-separated list of question types')
    parser.add_argument('--num-questions', type=int, required=True, help='Number of questions to generate')
    
    # Optional arguments
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], default='medium',
                      help='Question difficulty level')
    parser.add_argument('--flavour', help='Worksheet theme/flavour (e.g. interview-prep)')
    
    # Output options
    parser.add_argument('-o', '--output', type=Path, default='worksheet_config.yaml',
                      help='Output file path')
    parser.add_argument('--format', choices=['yaml', 'json'], default='yaml',
                      help='Output file format')

    args = parser.parse_args()
    
    generator = WorksheetGenerator()
    
    config = generator.generate_config(
        subject=args.subject,
        language=args.language,
        selected_topics=args.topics.split(','),
        selected_question_types=args.question_types.split(','),
        num_questions=args.num_questions,
        flavour=args.flavour,
        difficulty=args.difficulty
    )
    
    # Save output
    try:
        with open(args.output, 'w') as f:
            if args.format == 'yaml':
                yaml.dump(config, f)
            else:
                import json
                json.dump(config, f, indent=2)
        print(f"Configuration saved to {args.output}")
    except Exception as e:
        print(f"Error saving config: {e}")
        exit(1)

if __name__ == '__main__':
    main()
