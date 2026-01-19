"""
Niche-specific templates and configurations
Enables ViraLens to work across any content category
"""

NICHE_TEMPLATES = {
    'royal_family': {
        'name': 'Royal Family & Meghan Markle',
        'icon': '👑',
        'default_keywords': [
            'Meghan Markle',
            'Prince Harry',
            'Royal Family',
            'Archewell Foundation'
        ],
        'default_subreddits': [
            'SaintMeghanMarkle',
            'RoyalsGossip',
            'BritishRoyals'
        ],
        'competitor_examples': [
            'River (@HRHRiver)',
            'Jessica Talks Tea',
            'Lena Exposed'
        ],
        'content_angles': [
            'Breaking News',
            'Body Language Analysis',
            'Timeline Deep Dive',
            'Protocol Breakdown',
            'Celebrity Crossover'
        ]
    },
    'tech': {
        'name': 'Tech & AI News',
        'icon': '💻',
        'default_keywords': [
            'ChatGPT',
            'OpenAI',
            'AI News',
            'Tech Layoffs',
            'Silicon Valley'
        ],
        'default_subreddits': [
            'technology',
            'artificial',
            'OpenAI',
            'MachineLearning'
        ],
        'competitor_examples': [
            'MKBHD',
            'Linus Tech Tips',
            'The AI Breakdown'
        ],
        'content_angles': [
            'Product Review',
            'Tutorial',
            'Industry Analysis',
            'Controversy Breakdown',
            'Prediction & Forecast'
        ]
    },
    'finance': {
        'name': 'Finance & Investing',
        'icon': '💰',
        'default_keywords': [
            'Stock Market',
            'Bitcoin',
            'Cryptocurrency',
            'Real Estate',
            'Inflation'
        ],
        'default_subreddits': [
            'investing',
            'stocks',
            'CryptoCurrency',
            'wallstreetbets'
        ],
        'competitor_examples': [
            'Graham Stephan',
            'Andrei Jikh',
            'Meet Kevin'
        ],
        'content_angles': [
            'Market Analysis',
            'Investment Strategy',
            'Portfolio Review',
            'Breaking Financial News',
            'Economic Forecast'
        ]
    },
    'health_fitness': {
        'name': 'Health & Fitness',
        'icon': '💪',
        'default_keywords': [
            'Weight Loss',
            'Workout Routine',
            'Intermittent Fasting',
            'Supplements',
            'Nutrition'
        ],
        'default_subreddits': [
            'Fitness',
            'loseit',
            'intermittentfasting',
            'nutrition'
        ],
        'competitor_examples': [
            'Athlean-X',
            'Jeremy Ethier',
            'Thomas DeLauer'
        ],
        'content_angles': [
            'Science-Based Review',
            'Myth Busting',
            'Workout Tutorial',
            'Diet Plan',
            'Transformation Story'
        ]
    },
    'gaming': {
        'name': 'Gaming & Esports',
        'icon': '🎮',
        'default_keywords': [
            'Call of Duty',
            'Fortnite',
            'League of Legends',
            'Gaming News',
            'Game Reviews'
        ],
        'default_subreddits': [
            'gaming',
            'Games',
            'pcgaming',
            'leagueoflegends'
        ],
        'competitor_examples': [
            'PewDiePie',
            'Ninja',
            'Shroud'
        ],
        'content_angles': [
            'Game Review',
            'Gameplay Commentary',
            'Tips & Tricks',
            'Drama Coverage',
            'Tournament Analysis'
        ]
    },
    'business': {
        'name': 'Business & Entrepreneurship',
        'icon': '📈',
        'default_keywords': [
            'Startup',
            'Business Ideas',
            'Entrepreneurship',
            'Side Hustle',
            'E-commerce'
        ],
        'default_subreddits': [
            'Entrepreneur',
            'smallbusiness',
            'startups',
            'BusinessHub'
        ],
        'competitor_examples': [
            'Ali Abdaal',
            'Pat Flynn',
            'Gary Vee'
        ],
        'content_angles': [
            'Case Study',
            'How I Made',
            'Business Breakdown',
            'Strategy Analysis',
            'Failure Story'
        ]
    },
    'custom': {
        'name': 'Custom Niche',
        'icon': '✨',
        'default_keywords': [],
        'default_subreddits': [],
        'competitor_examples': [],
        'content_angles': [
            'Breaking News',
            'Deep Analysis',
            'Tutorial',
            'Review',
            'Commentary'
        ]
    }
}

def get_niche_config(niche_id: str) -> dict:
    """Get configuration for a specific niche"""
    return NICHE_TEMPLATES.get(niche_id, NICHE_TEMPLATES['custom'])

def get_available_niches() -> list:
    """Get list of available niches"""
    return [
        {'id': key, 'name': val['name'], 'icon': val['icon']}
        for key, val in NICHE_TEMPLATES.items()
    ]
