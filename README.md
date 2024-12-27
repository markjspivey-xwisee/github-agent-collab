# GitHub Agent Collaboration

A multi-agent system demonstrating autonomous collaboration through GitHub workflows. Different agents work together to develop, review, and maintain code through pull requests and code reviews.

## Agent Roles

1. **SpecificationAgent**: Creates and maintains project specifications
2. **DeveloperAgent**: Implements features based on specifications
3. **TestAgent**: Creates test cases and ensures test coverage
4. **ReviewAgent**: Reviews pull requests and provides feedback
5. **MergeAgent**: Makes final decisions on merging PRs

## Architecture

The system uses a modular architecture where each agent operates independently but collaborates through GitHub's PR system:

```
├── agents/           # Agent implementations
├── specifications/   # Project specifications
├── tests/           # Test suite
├── src/             # Main project source code
└── github/          # GitHub integration utilities
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure GitHub credentials:
```bash
cp .env.example .env
# Edit .env with your GitHub tokens
```

3. Run the agent system:
```bash
python main.py
