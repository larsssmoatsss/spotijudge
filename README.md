# spotijudge - Your Personal Music Taste Critic

A retro-styled web application that analyzes your Spotify listening habits through the lens of music critic culture. Connect your Spotify account to get your music taste "reviewed" with a custom scoring algorithm that judges your musical choices across multiple factors.

## Screenshots

### Landing Page
![Spotijudge Landing Page](static/images/spotijudge_landing.png)

### Review Interface
![Spotijudge Review Interface](static/images/spotijudge_review.png)

### Results Page
![Spotijudge Results Page](static/images/spotijudge_results.png)

## Features

- **Spotify OAuth Integration**: Secure authentication with Spotify Web API
- **Advanced Music Analysis**: Multi-factor scoring algorithm analyzing:
  - Genre diversity and "coolness" factor (70+ genres classified)
  - Artist and track popularity metrics
  - Follower count tiers
  - Content explicitness
- **Retro Gaming Interface**: Pixel-art inspired UI with interactive dialogue system
- **Three-Page User Flow**: Landing page → Track-by-track reviews → Comprehensive results
- **Suspenseful Experience**: Individual track scores revealed during review, final score saved for dramatic results page
- **Session-based Navigation**: Persistent state management for seamless browsing
- **Custom Visual Elements**: Themed scrollbars, glowing titles, and hover effects
- **Responsive Design**: Works on desktop and mobile devices

## Technologies Used

- **Backend**: Python 3.7+, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **API**: Spotify Web API (OAuth 2.0)
- **Styling**: Custom CSS with Google Fonts (Press Start 2P)
- **Session Management**: Flask sessions for state persistence

## How It Works

1. **Authentication**: Users authenticate via Spotify OAuth
2. **Data Collection**: App fetches user's top 20 tracks and detailed artist information
3. **Track-by-Track Review**: Users cycle through individual tracks with personalized scoring
4. **Scoring Algorithm**: Each track receives a "cool score" based on:
   - **Genre Bonus**: +50 points for "cool" genres (metal, experimental, underground hip-hop, etc.)
   - **Popularity Scaling**: Lower popularity = higher score (rewards discovering underground music)
   - **Artist Followers**: Fewer followers = bonus points (supports smaller artists)
   - **Track Popularity**: Less mainstream tracks score higher
   - **Explicit Content**: +5 point bonus
5. **Results Revelation**: Final page reveals overall score with commentary and complete track breakdown
6. **Navigation Options**: Review tracks again or start completely over

## User Experience Flow

### Landing Page
- Animated title with wave effects
- Clear explanation of the review process
- Character preview with speech bubble
- Spotify connection with privacy disclaimer

### Review Interface
- RPG-style layout with character and track info panels
- Individual track details including genres and popularity
- Cool score for each track (or "not scored" for tracks without genre data)
- Progress indicator showing current position
- Interactive dialogue system with clickable progression

### Results Page
- Dramatic score reveal with pulsing animation
- Music critic-style commentary based on final score:
  - 90%+: "absolutely legendary taste!"
  - 80-89%: "solid taste!"
  - 70-79%: "decent taste, but room for exploration"
  - 60-69%: "on the right track"
  - 50-59%: "pretty mainstream, time to explore"
  - <50%: "very mainstream, let's find hidden gems"
- Statistics breakdown (scored vs unscored tracks)
- Complete scrollable tracklist sorted by score
- Navigation options to review again or start over

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Spotify account (free or premium)
- Spotify Developer App credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/larsssmoatsss/spotijudge.git
   cd spotijudge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Spotify Developer App**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Add `http://localhost:5000/callback` to Redirect URIs
   - Note your Client ID and Client Secret

4. **Configure credentials**
   - Copy `config.example.json` to `config.json`
   - Fill in your Spotify API credentials:
   ```json
   {
       "SPOTIFY_CLIENT_ID": "your_client_id_here",
       "SPOTIFY_CLIENT_SECRET": "your_client_secret_here", 
       "SPOTIFY_REDIRECT_URI": "http://localhost:5000/callback"
   }
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## Scoring System

The "cool score" algorithm evaluates tracks on multiple criteria:

### Genre Classification
70+ "cool" genres including:
- **Metal variants**: deathcore, black metal, doom metal, mathcore
- **Electronic**: IDM, breakcore, dark ambient, industrial
- **Hip-hop**: experimental hip hop, underground rap, horrorcore
- **Rock/Punk**: post-hardcore, shoegaze, noise rock, math rock
- **Jazz/Soul**: jazz fusion, alternative R&B
- **And many more underground/experimental genres**

### Scoring Breakdown
- **Genre Bonus**: 50 points for tracks in "cool" genres
- **Artist Popularity**: 2-18 points (inverse scale - less popular = more points)
- **Follower Count**: 6-16 points (supports smaller artists)
- **Track Popularity**: 1-11 points (underground tracks favored)
- **Explicit Content**: 5 point bonus
- **Maximum Score**: 100 points per track

## Design Features

- **Retro Gaming Aesthetic**: Inspired by classic RPG dialogue systems
- **Custom Character**: Temporary placeholder sprite (final artwork planned)
- **Interactive Elements**: Clickable dialogue progression with hover effects
- **Responsive Grid Layout**: Adapts to different screen sizes
- **Typography**: Press Start 2P font for authentic retro feel
- **Color Scheme**: Dark theme with Spotify green accents (#1db954)
- **Custom Scrollbars**: Themed scrollbars matching the green aesthetic
- **Animated Elements**: Glowing titles, pulsing scores, and smooth transitions

## Project Structure

```
spotijudge/
│
├── app.py                    # Main Flask application and scoring logic
├── config.json              # Spotify API credentials (gitignored)
├── config.example.json      # Configuration template
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
│
├── static/
│   ├── styles.css          # Complete UI styling
│   ├── script.js           # Frontend interactivity
│   └── images/
│       ├── fantanogreen.png # Temporary character sprite (placeholder)
│       ├── spotijudge_landing.png # Landing page screenshot
│       ├── spotijudge_review.png # Review interface screenshot
│       └── spotijudge_results.png # Results page screenshot
│
└── templates/
    ├── landing.html        # Landing page with animated elements
    ├── index.html          # Review interface
    └── results.html        # Final results page
```

## Technical Highlights

### OAuth Implementation
- Complete Spotify OAuth 2.0 flow
- Secure token exchange and session management
- Proper scope handling for user data access

### Data Processing
- Multiple API calls for comprehensive user analysis
- Artist metadata aggregation and caching
- Complex scoring algorithm with weighted factors

### Frontend Architecture
- Session-based state management
- Interactive UI with smooth navigation
- Responsive design principles
- Custom CSS animations and effects

### User Experience Design
- Suspenseful score revelation system
- Clear progress indicators
- Error handling and user feedback
- Mobile-optimized interface

## Future Enhancements

- [ ] Add playlist generation based on scoring recommendations
- [ ] Implement user comparison features ("whose taste is cooler?")
- [ ] Add detailed analytics and visualization charts
- [ ] Create shareable results with social media integration
- [ ] Expand genre classification system
- [ ] Add audio preview integration
- [ ] Implement user accounts and score history
- [ ] Deploy as a public web application

## What I Learned

- **Full-stack Development**: End-to-end web application creation with Flask
- **API Authentication**: OAuth 2.0 implementation and security best practices
- **Data Analysis**: Creating meaningful metrics from raw API data
- **Algorithm Development**: Designing scoring systems with multiple weighted variables
- **UI/UX Design**: Building engaging, themed user interfaces
- **Session Management**: Handling user state across HTTP requests
- **Responsive Design**: Creating mobile-friendly web applications
- **User Experience Flow**: Crafting suspenseful, engaging user journeys

## Contributing

This is a personal learning project showcasing full-stack development skills. Feedback and suggestions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is open source and available under the [MIT License](https://opensource.org/license/mit).

---

**Built with care by Lars Moats** | *Demonstrating full-stack development, API integration, and creative algorithm design*

*Connect with me on [LinkedIn](https://www.linkedin.com/in/larsmoats/)*