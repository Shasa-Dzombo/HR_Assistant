# HR Assistant System

An AI-powered HR Assistant system with specialized bots for various HR tasks including recruitment, employee management, onboarding, and performance tracking.

## Features

- **Recruitment Bot**: Automated candidate screening, interview scheduling, and job posting management
- **Employee Management Bot**: Employee record management, policy queries, and document handling
- **Onboarding Bot**: New hire process automation and document collection
- **Performance Bot**: Performance review automation and goal tracking
- **Node-based Workflow System**: Chainable processes for complex HR operations
- **RESTful API**: Easy integration with existing HR systems

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the application:
   ```bash
   python src/main.py
   ```

## Project Structure

```
HR_Assistant/
├── src/
│   ├── bots/              # AI bot implementations
│   ├── nodes/             # Workflow node system
│   ├── utils/             # Utility functions
│   ├── models/            # Data models
│   ├── api/               # API endpoints
│   └── config/            # Configuration
├── tests/                 # Test files
├── docs/                  # Documentation
└── migrations/            # Database migrations
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## License

MIT License