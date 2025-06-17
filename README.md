
// ===== README.MD =====
# AI Cold Calling Coach - Flask Implementation

A comprehensive AI-powered cold calling training platform designed for non-native Spanish-speaking Sales Development Representatives (SDRs) to practice English cold calling skills.

## 🚀 Features

- **5 Progressive Roleplay Modules**: From basic openers to full cold call simulations
- **AI-Powered Conversations**: Realistic prospect interactions using GPT-4
- **Voice-Based Training**: Speech recognition and text-to-speech integration
- **Real-Time Coaching**: Instant feedback on sales techniques, grammar, and pronunciation
- **Progress Tracking**: Detailed analytics and unlock system
- **Multiple Training Modes**: Practice, Marathon (10 calls), and Legend (6 perfect calls)

## 🏗️ Technology Stack

- **Backend**: Flask + Python
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **AI**: OpenAI GPT-4
- **Text-to-Speech**: ElevenLabs
- **Email**: Resend API
- **Frontend**: Vanilla JavaScript + Bootstrap 5
- **Deployment**: Vercel

## 📋 Prerequisites

- Python 3.8+
- Node.js (for development tools)
- Supabase account
- OpenAI API key
- ElevenLabs API key
- Resend API key

## 🛠️ Development Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd cold-calling-coach

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# Flask
FLASK_SECRET_KEY=your-super-secret-key-here

# Supabase
REACT_APP_SUPABASE_URL=your-supabase-url
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key

# OpenAI
REACT_APP_OPENAI_API_KEY=your-openai-api-key

# ElevenLabs
REACT_APP_ELEVENLABS_API_KEY=your-elevenlabs-api-key
REACT_APP_ELEVENLABS_VOICE_ID=your-voice-id

# Resend
REACT_APP_RESEND_API_KEY=your-resend-api-key

# App Config
REACT_APP_APP_URL=http://localhost:3001
REACT_APP_ADMIN_EMAIL=admin@yourdomain.com
```

### 3. Database Setup

1. Create a new Supabase project
2. Run the SQL schema from `migrations/supabase_schema.sql`
3. Enable Row Level Security (RLS) on all tables
4. Configure authentication settings in Supabase dashboard

### 4. Run Development Server

```bash
# Start the Flask development server
python api/app.py

# Server will run on http://localhost:3001
```

### 5. Verify Setup

1. Visit `http://localhost:3001`
2. Register a new account
3. Verify email functionality
4. Test voice recognition (requires HTTPS in production)

## 📁 Project Structure

```
cold-calling-coach/
├── api/                     # Flask backend
│   ├── routes/             # API routes
│   ├── services/           # External service integrations
│   ├── models/             # Data models
│   └── utils/              # Utility functions
├── static/                 # Frontend assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── images/            # Static images
├── templates/              # HTML templates
├── migrations/             # Database schema
└── requirements.txt        # Python dependencies
```

## 🚀 Deployment

### Vercel Deployment

1. **Prepare for deployment**:
   ```bash
   # Ensure all environment variables are set
   # Test the application locally first
   ```

2. **Deploy to Vercel**:
   ```bash
   # Install Vercel CLI
   npm i -g vercel

   # Deploy
   vercel

   # Set environment variables in Vercel dashboard
   ```

3. **Configure domains and SSL**:
   - Voice recognition requires HTTPS
   - Configure custom domain if needed
   - Verify SSL certificate

### Environment Variables in Vercel

Set these in your Vercel dashboard:

- `FLASK_SECRET_KEY`
- `REACT_APP_SUPABASE_URL`
- `REACT_APP_SUPABASE_ANON_KEY`
- `REACT_APP_OPENAI_API_KEY`
- `REACT_APP_ELEVENLABS_API_KEY`
- `REACT_APP_ELEVENLABS_VOICE_ID`
- `REACT_APP_RESEND_API_KEY`
- `REACT_APP_APP_URL`
- `REACT_APP_ADMIN_EMAIL`

## 🔧 Configuration

### Access Levels

- **Limited Trial**: 3 hours lifetime, 7 days from signup
- **Unlimited Basic**: 50 hours/month, 24-hour unlocks
- **Unlimited Pro**: 50 hours/month, permanent unlocks

### Roleplay Progression

1. **Opener + Early Objections** (Always available)
2. **Pitch + Objections + Close** (Unlock: Complete #1 Marathon)
3. **Warm-up Challenge** (Unlock: Complete #2 Marathon)  
4. **Full Cold Call Simulation** (Unlock: Pass #3)
5. **Power Hour Challenge** (Unlock: Complete #4)

## 🧪 Testing

### Manual Testing Checklist

- [ ] User registration and email verification
- [ ] Login/logout functionality
- [ ] Voice recognition in supported browsers
- [ ] Text-to-speech playback
- [ ] Roleplay progression and unlocks
- [ ] Usage limit enforcement
- [ ] Coaching feedback generation

### Browser Compatibility

- Chrome/Edge: Full support (recommended)
- Firefox: Limited voice recognition
- Safari: Partial support
- Mobile: Voice features may be limited

## 🔒 Security Considerations

- All API routes are protected with authentication
- Row Level Security (RLS) enabled in Supabase
- Environment variables stored securely
- HTTPS required for voice features
- Input validation on all user data

## 📊 Monitoring and Analytics

- User registration and activity tracking
- Session success rates and duration
- Usage patterns and limits
- Error logging and monitoring

## 🆘 Troubleshooting

### Common Issues

1. **Voice recognition not working**:
   - Ensure HTTPS is enabled
   - Check browser permissions
   - Verify microphone access

2. **API rate limits**:
   - Monitor OpenAI usage
   - Implement request queuing if needed
   - Optimize prompt efficiency

3. **Database connection issues**:
   - Verify Supabase credentials
   - Check RLS policies
   - Monitor connection limits

### Performance Optimization

- Implement audio caching for common responses
- Optimize database queries
- Use CDN for static assets
- Monitor serverless function execution time

## 📈 Scaling Considerations

- Database connection pooling
- Redis caching for sessions
- Load balancing for high traffic
- CDN integration for global performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[License information here]

## 📞 Support

For technical support or questions:
- Email: support@coldcallingcoach.com
- Documentation: [Link to docs]
- GitHub Issues: [Repository issues page]