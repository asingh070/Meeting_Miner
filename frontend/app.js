// API Base URL - Backend API server
const API_BASE = 'http://127.0.0.1:5000';

// Global state
let currentMeetingId = null;
let chatMessages = [];
let meetings = [];
let currentChatMeetingId = null; // Track which meeting ID is being used for chat (deprecated)
let currentChatProjectName = null; // Track which project name is being used for chat

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    loadMeetings();
    loadConfig();
    // Clear chat history on page load
    clearChatHistory();
});

// Navigation
function showPage(pageName, event) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected page
    document.getElementById(pageName + '-page').classList.add('active');
    
    // Activate corresponding nav link
    if (event && event.target && event.target.classList.contains('nav-link')) {
        event.target.classList.add('active');
    } else {
        // Find the button by page name
        const buttons = document.querySelectorAll('.nav-link');
        buttons.forEach((btn, index) => {
            const pages = ['upload', 'results', 'chatbot', 'history'];
            if (pages[index] === pageName) {
                btn.classList.add('active');
            }
        });
    }
    
    // Clear chat history when switching away from chatbot page
    if (pageName !== 'chatbot') {
        clearChatHistory();
    }
    
    // Load data for specific pages
    if (pageName === 'results' || pageName === 'chatbot') {
        loadMeetings();
    }
    if (pageName === 'chatbot') {
        // Clear chat history when entering chatbot page (fresh start)
        clearChatHistory();
    }
    if (pageName === 'history') {
        loadHistory();
    }
}

// File Upload
function initializeFileUpload() {
    const fileUploadArea = document.getElementById('file-upload-area');
    const fileInput = document.getElementById('file-input');
    
    fileUploadArea.addEventListener('click', () => fileInput.click());
    fileUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadArea.style.background = '#f0f2ff';
    });
    fileUploadArea.addEventListener('dragleave', () => {
        fileUploadArea.style.background = '#f8f9ff';
    });
    fileUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadArea.style.background = '#f8f9ff';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    const fileNameDiv = document.getElementById('file-name');
    fileNameDiv.textContent = `Selected: ${file.name}`;
    fileNameDiv.style.display = 'block';
    
    // Store file for processing
    window.selectedFile = file;
}

// Process Meeting
async function processMeeting() {
    const fileInput = document.getElementById('file-input');
    const transcriptText = document.getElementById('transcript-text').value;
    const meetingTitle = document.getElementById('meeting-title').value;
    const resultDiv = document.getElementById('upload-result');
    const processBtn = document.getElementById('process-btn');
    
    if (!window.selectedFile && !transcriptText.trim()) {
        showResult(resultDiv, 'Please upload a file or paste transcript text.', 'error');
        return;
    }
    
    processBtn.disabled = true;
    processBtn.textContent = 'Processing...';
    resultDiv.className = 'result-message';
    resultDiv.style.display = 'none';
    
    try {
        let transcript = transcriptText;
        let transcriptJson = null;
        
        if (window.selectedFile) {
            const fileContent = await readFile(window.selectedFile);
            if (window.selectedFile.name.endsWith('.json')) {
                transcriptJson = JSON.parse(fileContent);
                transcript = fileContent;
            } else {
                transcript = fileContent;
            }
        }
        
        const projectName = document.getElementById('project-name').value;
        
        const response = await fetch(`${API_BASE}/api/meetings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transcript: transcript,
                title: meetingTitle || null,
                project_name: projectName || null,
                transcript_json: transcriptJson
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentMeetingId = data.result.meeting_id;
            const summary = data.result.summary ? data.result.summary.substring(0, 500) : '';
            const projectDetails = data.result.project_details || data.result.projects || [];
            const projectCount = projectDetails.length;
            const projectName = data.result.project_name || '';
            
            // Format summary for display
            const formattedSummary = summary ? formatChatMessage(summary + (data.result.summary.length > 500 ? '...' : '')) : '';
            
            // Create formatted success message
            const successHtml = `
                <div style="margin-bottom: 12px;">
                    <strong>✅ Meeting processed successfully!</strong><br>
                    <strong>Meeting ID:</strong> ${data.result.meeting_id}
                    ${projectName ? `<br><strong>Project:</strong> ${projectName}` : ''}
                </div>
                ${formattedSummary ? `
                <div style="margin-bottom: 12px;">
                    <strong>Quick Summary:</strong>
                    <div class="formatted-summary" style="margin-top: 8px;">${formattedSummary}</div>
                </div>
                ` : ''}
                <div style="margin-bottom: 15px;">
                    <strong>Found ${projectCount} project detail(s)</strong>
                </div>
                <div style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="viewMeeting(${data.result.meeting_id})" style="width: 100%; padding: 12px; font-size: 1em;">
                        View Full Results →
                    </button>
                </div>
            `;
            
            showResult(resultDiv, successHtml, 'success', true);
            
            // Clear form
            document.getElementById('transcript-text').value = '';
            document.getElementById('meeting-title').value = '';
            document.getElementById('project-name').value = '';
            document.getElementById('file-name').style.display = 'none';
            window.selectedFile = null;
            fileInput.value = '';
            
            // Reload meetings
            loadMeetings();
        } else {
            showResult(resultDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        let errorMessage = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = `Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running.`;
        }
        showResult(resultDiv, `Error processing meeting: ${errorMessage}`, 'error');
        console.error('API Error:', error);
    } finally {
        processBtn.disabled = false;
        processBtn.textContent = 'Process Meeting';
    }
}

function readFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

function showResult(element, message, type, isHtml = false) {
    if (isHtml) {
        element.innerHTML = message;
    } else {
        element.textContent = message;
    }
    element.className = `result-message ${type}`;
    element.style.display = 'block';
}

// Load Meetings
async function loadMeetings() {
    try {
        const response = await fetch(`${API_BASE}/api/meetings`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            meetings = data.meetings;
            populateMeetingSelects();
        } else {
            console.error('API Error:', data.error);
        }
    } catch (error) {
        console.error('Error loading meetings:', error);
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            console.error(`Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running.`);
        }
    }
}

function populateMeetingSelects() {
    const meetingSelect = document.getElementById('meeting-select');
    
    if (meetingSelect) {
        meetingSelect.innerHTML = '<option value="">Select a meeting...</option>';
        
        meetings.forEach(meeting => {
            const option = document.createElement('option');
            option.value = meeting.id;
            const displayText = meeting.project_name 
                ? `${meeting.id} - ${meeting.title || 'Untitled'} (${meeting.project_name})`
                : `${meeting.id} - ${meeting.title || 'Untitled'}`;
            option.textContent = displayText;
            meetingSelect.appendChild(option);
        });
    }
}

// Load Meeting Details
async function loadMeetingDetails() {
    const meetingId = document.getElementById('meeting-select').value;
    const resultsContent = document.getElementById('results-content');
    
    if (!meetingId) {
        resultsContent.innerHTML = '<div class="info-message">Select a meeting to view results</div>';
        return;
    }
    
    resultsContent.innerHTML = '<div class="spinner active"></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/meetings/${meetingId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayMeetingResults(data.meeting);
        } else {
            resultsContent.innerHTML = `<div class="result-message error">${data.error}</div>`;
        }
    } catch (error) {
        let errorMessage = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = `Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running.`;
        }
        resultsContent.innerHTML = `<div class="result-message error">Error loading meeting: ${errorMessage}</div>`;
        console.error('API Error:', error);
    }
}

function displayMeetingResults(meeting) {
    const resultsContent = document.getElementById('results-content');
    
    let html = `
        <div class="meeting-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                <div>
                    <h3>${meeting.title || 'Untitled Meeting'}</h3>
                    ${meeting.project_name ? `<div style="margin-top: 8px; padding: 6px 12px; background: rgba(139, 92, 246, 0.2); border-radius: 6px; display: inline-block; border: 1px solid rgba(139, 92, 246, 0.4);">
                        <strong style="color: #a78bfa;">Project:</strong> <span style="color: rgba(255, 255, 255, 0.9);">${meeting.project_name}</span>
                    </div>` : ''}
                </div>
            </div>
            <div class="date">Processed on: ${meeting.created_at || 'Unknown'}</div>
        </div>
        
        <div class="tabs-container">
            <div class="tab-headers">
                <div class="tab-header active" onclick="showTab('summary')">Summary</div>
                <div class="tab-header" onclick="showTab('project-details')">Project Details</div>
                <div class="tab-header" onclick="showTab('pain-points')">Pain Points</div>
                <div class="tab-header" onclick="showTab('health')">Health Signals</div>
                <div class="tab-header" onclick="showTab('pulse')">Company Pulse</div>
                <div class="tab-header" onclick="showTab('ideas-scope')">Ideas and Scope</div>
            </div>
            
            <div id="summary-tab" class="tab-content active">
                <h3 style="margin-bottom: 15px;">Executive Summary</h3>
                <div class="formatted-summary">${meeting.summary ? formatChatMessage(meeting.summary) : '<p>No summary available.</p>'}</div>
            </div>
            
            <div id="project-details-tab" class="tab-content">
                <h3 style="margin-bottom: 15px;">Project Details</h3>
                ${displayProjectDetails(meeting.project_details || meeting.projects || [])}
            </div>
            
            <div id="pain-points-tab" class="tab-content">
                <h3>Project-Specific Pain Points</h3>
                ${displayPainPoints(meeting.pain_points || {})}
            </div>
            
            <div id="health-tab" class="tab-content">
                <h3>Project Health Signals</h3>
                <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 20px; font-size: 0.95em;">
                    Owners, blockers, and risks identified from the meeting transcript
                </p>
                ${displayHealthSignals(meeting.health_signals || {})}
            </div>
            
            <div id="pulse-tab" class="tab-content">
                <h3>Company Pulse</h3>
                <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 20px; font-size: 0.95em;">
                    Sentiment, tone, and behavioral cues extracted from meeting conversations
                </p>
                ${displayPulse(meeting.pulse || {}, meeting.overall_sentiment || 'neutral')}
            </div>
            
            <div id="ideas-scope-tab" class="tab-content">
                <h3>Ideas and Scope</h3>
                <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 20px; font-size: 0.95em;">
                    External ideas, opportunities, and scope for new projects or initiatives that can be built based on meeting discussions
                </p>
                ${displayExternalIdeasScope(meeting.external_ideas_scope || meeting.ideas_proposals || [])}
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

function showTab(tabName) {
    document.querySelectorAll('.tab-header').forEach(header => header.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}

function displayProjectDetails(projectDetails) {
    if (!projectDetails || projectDetails.length === 0) {
        return '<div class="info-message">No project details identified in this meeting.</div>';
    }
    
    return `
        <div style="margin-bottom: 20px; padding: 12px; background: rgba(6, 182, 212, 0.1); border-radius: 8px; border-left: 3px solid #06b6d4;">
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.9em; margin: 0;">
                <strong>Note:</strong> Project details include explicit project candidates, implicit projects from discussions, and even side-chat discussions that indicate potential initiatives.
            </p>
        </div>
        ${projectDetails.map(project => `
        <div class="project-card">
            <h4>📋 ${project.name || project.project_name || 'Unnamed Project'} <span class="status-badge status-${project.status || 'proposed'}">${project.status || 'proposed'}</span></h4>
            <p><strong>Description:</strong> ${project.description || 'N/A'}</p>
            <p><strong>Owner:</strong> ${project.owner || 'Unassigned'}</p>
            ${project.timeline_hints ? `<p><strong>Timeline:</strong> ${project.timeline_hints}</p>` : ''}
            ${project.blockers && project.blockers.length > 0 ? `
                <p><strong>Blockers:</strong></p>
                ${project.blockers.map(b => `<div class="blocker-item">${typeof b === 'object' ? b.description : b}</div>`).join('')}
            ` : ''}
            ${project.risks && project.risks.length > 0 ? `
                <p><strong>Risks:</strong></p>
                ${project.risks.map(r => `<div class="risk-item">${typeof r === 'object' ? r.description : r}</div>`).join('')}
            ` : ''}
        </div>
    `).join('')}
    `;
}

function displayHealthSignals(healthSignals) {
    const owners = healthSignals.owners || [];
    const blockers = healthSignals.blockers || [];
    const risks = healthSignals.risks || [];
    const commitments = healthSignals.commitment_signals || [];
    
    return `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <h4>Owners/Assignees</h4>
                ${owners.length > 0 ? owners.map(o => `<p>👤 ${o}</p>`).join('') : '<p class="info-message">No owners identified.</p>'}
            </div>
            <div>
                <h4>Blockers</h4>
                ${blockers.length > 0 ? blockers.map(b => {
                    const severity = typeof b === 'object' ? b.severity : 'medium';
                    const icon = severity === 'high' ? '🔴' : severity === 'medium' ? '🟡' : '🟢';
                    return `<div class="blocker-item">${icon} ${typeof b === 'object' ? b.description : b}</div>`;
                }).join('') : '<p class="info-message">No blockers identified.</p>'}
            </div>
        </div>
        <div>
            <h4>Risks</h4>
            ${risks.length > 0 ? risks.map(r => {
                const severity = typeof r === 'object' ? r.severity : 'medium';
                const icon = severity === 'high' ? '🔴' : severity === 'medium' ? '🟡' : '🟢';
                return `<div class="risk-item">${icon} ${typeof r === 'object' ? r.description : r}</div>`;
            }).join('') : '<p class="info-message">No risks identified.</p>'}
        </div>
        <div style="margin-top: 20px;">
            <h4>Commitment Signals</h4>
            ${commitments.length > 0 ? commitments.map(c => 
                `<div class="info-message">💬 "${typeof c === 'object' ? c.text : c}" → ${typeof c === 'object' ? c.interpretation : ''}</div>`
            ).join('') : '<p class="info-message">No commitment signals identified.</p>'}
        </div>
    `;
}

function displayPulse(pulse, overallSentiment) {
    const sentiment = overallSentiment || pulse.overall_sentiment || 'neutral';
    const sentimentScore = pulse.sentiment_score || 0.5;
    const tone = pulse.tone || [];
    const speakerSentiments = pulse.speaker_sentiments || [];
    const behavioralCues = pulse.behavioral_cues || [];
    const insights = pulse.key_insights || [];
    
    const sentimentIcon = sentiment === 'positive' ? '😊' : sentiment === 'neutral' ? '😐' : '😟';
    const sentimentColor = sentiment === 'positive' ? '#10b981' : sentiment === 'neutral' ? '#6b7280' : '#ef4444';
    const percentage = (sentimentScore * 100).toFixed(0);
    
    return `
        <!-- Overall Employee Sentiment Section -->
        <div style="margin-bottom: 40px;">
            <h3 style="margin-bottom: 20px;">Overall Employee Sentiment</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; margin-bottom: 30px;">
                <div class="info-message" style="text-align: center; padding: 30px;">
                    <h4>Overall Employee Sentiment</h4>
                    <p style="font-size: 4em; margin: 20px 0;">${sentimentIcon}</p>
                    <p style="font-size: 1.5em; font-weight: 600; color: ${sentimentColor};">
                        ${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                    </p>
                    <p style="margin-top: 10px; color: rgba(255, 255, 255, 0.7);">${percentage}% positive</p>
                </div>
                <div class="info-message" style="padding: 30px;">
                    <h4>Sentiment Breakdown</h4>
                    <div style="margin-top: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Sentiment Score</span>
                            <span style="font-weight: 600;">${sentimentScore.toFixed(2)} / 1.0</span>
                        </div>
                        <div style="background: rgba(17, 24, 39, 0.6); border-radius: 8px; height: 20px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, ${sentimentColor}, ${sentimentColor}88); height: 100%; width: ${percentage}%; transition: width 0.5s;"></div>
                        </div>
                        <p style="margin-top: 15px; color: rgba(255, 255, 255, 0.7); font-size: 0.9em;">
                            ${sentiment === 'positive' ? 'Team sentiment is positive and optimistic.' : 
                              sentiment === 'neutral' ? 'Team sentiment is neutral and balanced.' : 
                              'Team sentiment shows concerns or challenges.'}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tone and Metrics -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
            <div class="info-message">
                <h4>Overall Sentiment</h4>
                <p style="font-size: 2em;">${sentimentIcon}</p>
                <p>${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}</p>
            </div>
            <div class="info-message">
                <h4>Sentiment Score</h4>
                <p style="font-size: 2em;">${sentimentScore.toFixed(2)}</p>
            </div>
            <div class="info-message">
                <h4>Tone</h4>
                <p>${tone.length > 0 ? tone.join(', ') : 'N/A'}</p>
            </div>
        </div>
        
        <!-- Per-Speaker Sentiment -->
        ${speakerSentiments.length > 0 ? `
            <div style="margin-bottom: 30px;">
                <h3 style="margin-bottom: 15px;">Per-Speaker Sentiment</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px;">
                    ${speakerSentiments.map(ss => {
                        const icon = ss.sentiment === 'positive' ? '😊' : ss.sentiment === 'neutral' ? '😐' : '😟';
                        return `
                            <div class="info-message" style="padding: 15px;">
                                <p style="font-weight: 600;">${icon} ${ss.speaker || 'Unknown'}</p>
                                <p style="font-size: 0.9em; color: rgba(255, 255, 255, 0.7); margin-top: 5px;">
                                    ${ss.sentiment.charAt(0).toUpperCase() + ss.sentiment.slice(1)}
                                </p>
                                ${ss.engagement_level ? `<p style="font-size: 0.85em; color: rgba(255, 255, 255, 0.6);">Engagement: ${ss.engagement_level}</p>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        ` : ''}
        
        <!-- Behavioral Cues -->
        ${behavioralCues.length > 0 ? `
            <div style="margin-top: 20px; margin-bottom: 30px;">
                <h3 style="margin-bottom: 15px;">Behavioral Cues</h3>
                ${behavioralCues.map(c => `
                    <div class="info-message" style="margin-bottom: 10px;">📊 [${typeof c === 'object' ? c.type : 'unknown'}] ${typeof c === 'object' ? c.cue : c}</div>
                `).join('')}
            </div>
        ` : ''}
        
        <!-- Key Insights -->
        ${insights.length > 0 ? `
            <div style="margin-top: 20px;">
                <h3 style="margin-bottom: 15px;">Key Insights</h3>
                ${insights.map(i => `<div class="result-message success" style="margin-bottom: 10px;">💡 ${i}</div>`).join('')}
            </div>
        ` : ''}
    `;
}

function displayPainPoints(painPoints) {
    const projectSpecific = painPoints.project_specific || [];
    const general = painPoints.general || [];
    
    let html = '';
    
    if (projectSpecific.length > 0) {
        html += '<div style="margin-bottom: 30px;"><h4>Project-Specific Pain Points</h4>';
        html += projectSpecific.map(pp => {
            const severity = pp.severity || 'medium';
            const severityIcon = severity === 'high' ? '🔴' : severity === 'medium' ? '🟡' : '🟢';
            return `
                <div class="project-card" style="border-left-color: ${severity === 'high' ? '#ef4444' : severity === 'medium' ? '#fbbf24' : '#10b981'};">
                    <h4>${severityIcon} ${pp.project || 'General'}</h4>
                    <p><strong>Pain Point:</strong> ${pp.pain_point}</p>
                    ${pp.impact ? `<p><strong>Impact:</strong> ${pp.impact}</p>` : ''}
                    <p><strong>Severity:</strong> <span class="status-badge status-${severity}">${severity}</span></p>
                </div>
            `;
        }).join('');
        html += '</div>';
    }
    
    if (general.length > 0) {
        html += '<div><h4>General Pain Points</h4>';
        html += general.map(pp => {
            const severity = pp.severity || 'medium';
            const severityIcon = severity === 'high' ? '🔴' : severity === 'medium' ? '🟡' : '🟢';
            return `
                <div class="project-card" style="border-left-color: ${severity === 'high' ? '#ef4444' : severity === 'medium' ? '#fbbf24' : '#10b981'};">
                    <h4>${severityIcon} ${pp.category || 'General'}</h4>
                    <p><strong>Pain Point:</strong> ${pp.pain_point}</p>
                    ${pp.impact ? `<p><strong>Impact:</strong> ${pp.impact}</p>` : ''}
                    <p><strong>Severity:</strong> <span class="status-badge status-${severity}">${severity}</span></p>
                </div>
            `;
        }).join('');
        html += '</div>';
    }
    
    if (projectSpecific.length === 0 && general.length === 0) {
        html = '<div class="info-message">No pain points identified in this meeting.</div>';
    }
    
    return html;
}

function displayOverallSentiment(overallSentiment, pulse) {
    const sentimentScore = pulse.sentiment_score || 0.5;
    const sentimentIcon = overallSentiment === 'positive' ? '😊' : overallSentiment === 'neutral' ? '😐' : '😟';
    const sentimentColor = overallSentiment === 'positive' ? '#10b981' : overallSentiment === 'neutral' ? '#6b7280' : '#ef4444';
    
    // Calculate percentage
    const percentage = (sentimentScore * 100).toFixed(0);
    
    return `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; margin-bottom: 30px;">
            <div class="info-message" style="text-align: center; padding: 30px;">
                <h4>Overall Employee Sentiment</h4>
                <p style="font-size: 4em; margin: 20px 0;">${sentimentIcon}</p>
                <p style="font-size: 1.5em; font-weight: 600; color: ${sentimentColor};">
                    ${overallSentiment.charAt(0).toUpperCase() + overallSentiment.slice(1)}
                </p>
                <p style="margin-top: 10px; color: rgba(255, 255, 255, 0.7);">${percentage}% positive</p>
            </div>
            <div class="info-message" style="padding: 30px;">
                <h4>Sentiment Breakdown</h4>
                <div style="margin-top: 20px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>Sentiment Score</span>
                        <span style="font-weight: 600;">${sentimentScore.toFixed(2)} / 1.0</span>
                    </div>
                    <div style="background: rgba(17, 24, 39, 0.6); border-radius: 8px; height: 20px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, ${sentimentColor}, ${sentimentColor}88); height: 100%; width: ${percentage}%; transition: width 0.5s;"></div>
                    </div>
                    <p style="margin-top: 15px; color: rgba(255, 255, 255, 0.7); font-size: 0.9em;">
                        ${overallSentiment === 'positive' ? 'Team sentiment is positive and optimistic.' : 
                          overallSentiment === 'neutral' ? 'Team sentiment is neutral and balanced.' : 
                          'Team sentiment shows concerns or challenges.'}
                    </p>
                </div>
            </div>
        </div>
        ${pulse.speaker_sentiments && pulse.speaker_sentiments.length > 0 ? `
            <div>
                <h4>Per-Speaker Sentiment</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; margin-top: 15px;">
                    ${pulse.speaker_sentiments.map(ss => {
                        const icon = ss.sentiment === 'positive' ? '😊' : ss.sentiment === 'neutral' ? '😐' : '😟';
                        return `
                            <div class="info-message" style="padding: 15px;">
                                <p style="font-weight: 600;">${icon} ${ss.speaker || 'Unknown'}</p>
                                <p style="font-size: 0.9em; color: rgba(255, 255, 255, 0.7); margin-top: 5px;">
                                    ${ss.sentiment.charAt(0).toUpperCase() + ss.sentiment.slice(1)}
                                </p>
                                ${ss.engagement_level ? `<p style="font-size: 0.85em; color: rgba(255, 255, 255, 0.6);">Engagement: ${ss.engagement_level}</p>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

function displayExternalIdeasScope(externalIdeasScope) {
    if (!externalIdeasScope || externalIdeasScope.length === 0) {
        return '<div class="info-message">No external ideas or scope identified in this meeting.</div>';
    }
    
    return `
        <div style="margin-bottom: 20px; padding: 12px; background: rgba(139, 92, 246, 0.1); border-radius: 8px; border-left: 3px solid #8b5cf6;">
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.9em; margin: 0;">
                <strong>Note:</strong> These are external ideas and opportunities that emerged from discussions - additional projects or initiatives that could be built beyond the main project scope.
            </p>
        </div>
        ${externalIdeasScope.map(idea => {
        const feasibility = idea.feasibility || 'medium';
        const feasibilityIcon = feasibility === 'high' ? '✅' : feasibility === 'medium' ? '⚠️' : '❌';
        return `
            <div class="project-card">
                <h4>💡 ${idea.idea || 'Untitled Idea'}</h4>
                <p><strong>Description:</strong> ${idea.description || 'No description available.'}</p>
                ${idea.scope ? `<p><strong>Scope:</strong> ${idea.scope}</p>` : ''}
                ${idea.potential_value ? `<p><strong>Potential Value:</strong> ${idea.potential_value}</p>` : ''}
                <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                    ${idea.suggested_by ? `<p><strong>Suggested by:</strong> ${idea.suggested_by}</p>` : ''}
                    <p><strong>Feasibility:</strong> ${feasibilityIcon} <span class="status-badge status-${feasibility}">${feasibility}</span></p>
                </div>
                ${idea.related_to ? `<p><strong>Related to:</strong> ${idea.related_to}</p>` : ''}
            </div>
        `;
    }).join('')}
    `;
}

// Chatbot
function updateChatScope() {
    const scope = document.querySelector('input[name="scope"]:checked').value;
    const projectSelectDiv = document.getElementById('project-select-chat');
    
    const previousProjectName = currentChatProjectName;
    
    if (scope === 'project') {
        projectSelectDiv.style.display = 'block';
        loadProjectsForChat();
        // Get the selected project name
        const selectedProjectName = document.getElementById('chat-project-select').value;
        currentChatProjectName = selectedProjectName || null;
    } else {
        projectSelectDiv.style.display = 'none';
        currentChatProjectName = null; // All meetings
    }
    
    // Clear chat history if project changed
    if (previousProjectName !== currentChatProjectName) {
        clearChatHistory();
    }
}

function onChatProjectChange() {
    const selectedProjectName = document.getElementById('chat-project-select').value;
    const previousProjectName = currentChatProjectName;
    currentChatProjectName = selectedProjectName || null;
    
    // Clear chat history if project changed
    if (previousProjectName !== currentChatProjectName) {
        clearChatHistory();
    }
}

async function loadProjectsForChat() {
    const projectSelect = document.getElementById('chat-project-select');
    if (!projectSelect) {
        console.error('chat-project-select element not found');
        return;
    }
    
    try {
        projectSelect.innerHTML = '<option value="">Loading projects...</option>';
        
        const response = await fetch(`${API_BASE}/api/projects`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.projects && data.projects.length > 0) {
            projectSelect.innerHTML = '<option value="">Select a project...</option>';
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.name;
                option.textContent = project.name + (project.count ? ` (${project.count} meeting${project.count > 1 ? 's' : ''})` : '');
                projectSelect.appendChild(option);
            });
        } else {
            projectSelect.innerHTML = '<option value="">No projects found</option>';
        }
    } catch (error) {
        console.error('Error loading projects:', error);
        let errorMessage = 'Error loading projects';
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = `Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running.`;
        }
        projectSelect.innerHTML = `<option value="">${errorMessage}</option>`;
    }
}

function clearChatHistory() {
    // Clear the chat messages array
    chatMessages = [];
    
    // Clear localStorage
    try {
        localStorage.removeItem('meetingminer_chat_history');
    } catch (e) {
        console.error('Error clearing chat history:', e);
    }
    
    // Clear the UI
    const chatMessagesDiv = document.getElementById('chat-messages');
    if (chatMessagesDiv) {
        chatMessagesDiv.innerHTML = '';
    }
    
    console.log('Chat history cleared for project:', currentChatProjectName);
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const question = chatInput.value.trim();
    
    if (!question) return;
    
    // Get project name if specific project selected
    const scope = document.querySelector('input[name="scope"]:checked').value;
    const projectName = scope === 'project' ? document.getElementById('chat-project-select').value : null;
    
    // Check if project changed and clear history if needed
    if (currentChatProjectName !== projectName) {
        currentChatProjectName = projectName;
        clearChatHistory();
    }
    
    if (scope === 'project' && !projectName) {
        addChatMessage('assistant', 'Please select a project first.');
        saveChatHistory();
        return;
    }
    
    // Add user message to chat
    addChatMessage('user', question);
    saveChatHistory();
    chatInput.value = '';
    
    // Show loading message (marked as temporary)
    const loadingId = addChatMessage('assistant', 'Thinking...', true);
    console.log('Loading message ID:', loadingId);
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                project_name: projectName || null
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading message - use multiple methods to ensure removal
        removeLoadingMessage(loadingId);
        
        // Add actual response
        if (data.success) {
            addChatMessage('assistant', data.response);
        } else {
            addChatMessage('assistant', `Error: ${data.error}`);
        }
        saveChatHistory();
    } catch (error) {
        // Remove loading message
        removeLoadingMessage(loadingId);
        
        let errorMessage = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = `Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running.`;
        }
        addChatMessage('assistant', `Error: ${errorMessage}`);
        saveChatHistory();
        console.error('API Error:', error);
    }
}

function removeLoadingMessage(loadingId) {
    // Method 1: Remove by ID
    if (loadingId) {
        const messageById = document.getElementById(loadingId);
        if (messageById) {
            console.log('Removing loading message by ID:', loadingId);
            messageById.remove();
            return;
        }
    }
    
    // Method 2: Remove all temporary messages (most reliable)
    const tempMessages = document.querySelectorAll('.temporary-message, [data-temporary="true"]');
    if (tempMessages.length > 0) {
        console.log('Removing', tempMessages.length, 'temporary message(s)');
        tempMessages.forEach(msg => {
            msg.remove();
        });
        return;
    }
    
    // Method 3: Remove last "Thinking..." message by content
    const chatMessagesDiv = document.getElementById('chat-messages');
    if (chatMessagesDiv) {
        const allMessages = Array.from(chatMessagesDiv.querySelectorAll('.chat-message.assistant'));
        // Search from end to beginning
        for (let i = allMessages.length - 1; i >= 0; i--) {
            const msgText = allMessages[i].textContent.trim();
            if (msgText === 'Thinking...') {
                console.log('Removing "Thinking..." message by content');
                allMessages[i].remove();
                return;
            }
        }
    }
    
    console.warn('Could not remove loading message with ID:', loadingId);
}

function formatChatMessage(content) {
    if (!content) return '';
    
    // Escape HTML to prevent XSS
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    let formatted = escapeHtml(content);
    
    // First, detect and format tables (markdown-style)
    formatted = formatTables(formatted);
    
    // Split content into blocks (paragraphs separated by double newlines)
    const blocks = formatted.split(/\n\s*\n/).filter(b => b.trim());
    let result = [];
    
    blocks.forEach(block => {
        // Skip if already formatted as table
        if (block.includes('<table')) {
            result.push(block);
            return;
        }
        
        const lines = block.split('\n').map(l => l.trim()).filter(l => l);
        let currentList = null;
        
        lines.forEach(line => {
            // Skip if already formatted as table row
            if (line.includes('<table') || line.includes('</table>') || line.includes('<tr>')) {
                result.push(line);
                return;
            }
            
            // Check for bullet points
            const bulletMatch = line.match(/^[-*•]\s+(.+)$/);
            if (bulletMatch) {
                if (!currentList || currentList.type !== 'ul') {
                    if (currentList) {
                        result.push(currentList.type === 'ul' ? '</ul>' : '</ol>');
                    }
                    currentList = { type: 'ul' };
                    result.push('<ul>');
                }
                result.push(`<li>${formatInlineText(bulletMatch[1])}</li>`);
                return;
            }
            
            // Check for numbered lists
            const numberMatch = line.match(/^(\d+)\.\s+(.+)$/);
            if (numberMatch) {
                if (!currentList || currentList.type !== 'ol') {
                    if (currentList) {
                        result.push(currentList.type === 'ul' ? '</ul>' : '</ol>');
                    }
                    currentList = { type: 'ol' };
                    result.push('<ol>');
                }
                result.push(`<li>${formatInlineText(numberMatch[2])}</li>`);
                return;
            }
            
            // Close list if we hit a non-list line
            if (currentList) {
                result.push(currentList.type === 'ul' ? '</ul>' : '</ol>');
                currentList = null;
            }
            
            // Regular paragraph
            result.push(`<p>${formatInlineText(line)}</p>`);
        });
        
        // Close any open list
        if (currentList) {
            result.push(currentList.type === 'ul' ? '</ul>' : '</ol>');
        }
    });
    
    return result.join('');
}

function formatTables(content) {
    const lines = content.split('\n');
    let result = [];
    let inTable = false;
    let tableRows = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check if line looks like a table row (contains pipes or tabs with multiple columns)
        const isTableRow = (line.includes('|') && line.split('|').length >= 3) ||
                          (line.includes('\t') && line.split('\t').length >= 2);
        
        // Check if line is a table separator (markdown style: |---|---|)
        const isTableSeparator = /^\|[\s\-:]+(\|[\s\-:]+)+\|$/.test(line) ||
                                 /^[\-\s]+$/.test(line) && line.length > 10;
        
        if (isTableRow && !isTableSeparator) {
            if (!inTable) {
                inTable = true;
                tableRows = [];
            }
            tableRows.push(line);
        } else if (isTableSeparator && inTable) {
            // This is the separator row, skip it but keep table open
            continue;
        } else {
            // Not a table row
            if (inTable) {
                // Close the table
                result.push(formatTableRows(tableRows));
                tableRows = [];
                inTable = false;
            }
            result.push(lines[i]); // Keep original line with spacing
        }
    }
    
    // Close any open table at the end
    if (inTable && tableRows.length > 0) {
        result.push(formatTableRows(tableRows));
    }
    
    return result.join('\n');
}

function formatTableRows(rows) {
    if (rows.length === 0) return '';
    
    let html = '<div class="table-container"><table>';
    
    rows.forEach((row, index) => {
        // Parse row - handle both pipe-separated and tab-separated
        let cells;
        if (row.includes('|')) {
            cells = row.split('|').map(c => c.trim()).filter(c => c);
        } else if (row.includes('\t')) {
            cells = row.split('\t').map(c => c.trim());
        } else {
            // Try to split by multiple spaces
            cells = row.split(/\s{2,}/).map(c => c.trim()).filter(c => c);
        }
        
        if (cells.length === 0) return;
        
        const tag = index === 0 ? 'th' : 'td';
        html += '<tr>';
        cells.forEach(cell => {
            html += `<${tag}>${formatInlineText(cell)}</${tag}>`;
        });
        html += '</tr>';
        
        // Add separator row after header
        if (index === 0 && rows.length > 1) {
            html += '<tr class="table-separator">';
            cells.forEach(() => {
                html += '<td></td>';
            });
            html += '</tr>';
        }
    });
    
    html += '</table></div>';
    return html;
}

function formatInlineText(text) {
    // Format bold text (**text**)
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Format italic text (_text_)
    text = text.replace(/_([^_]+)_/g, '<em>$1</em>');
    
    // Format code (backticks)
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    return text;
}

function addChatMessage(role, content, isTemporary = false) {
    const chatMessagesDiv = document.getElementById('chat-messages');
    if (!chatMessagesDiv) {
        console.error('Chat messages div not found!');
        return null;
    }
    
    // Generate unique ID with timestamp and random number
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${role}`;
    
    // Format content for assistant messages, plain text for user messages (security)
    if (role === 'assistant' && !isTemporary) {
        messageDiv.innerHTML = formatChatMessage(content);
    } else {
        messageDiv.textContent = content;
    }
    
    // Add temporary class and data attribute for loading messages
    if (isTemporary) {
        messageDiv.classList.add('temporary-message');
        messageDiv.setAttribute('data-temporary', 'true');
    }
    
    chatMessagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom after DOM update
    setTimeout(() => {
        chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
    }, 10);
    
    // Store in chat history (except temporary messages and "Thinking...")
    if (!isTemporary && content !== 'Thinking...') {
        chatMessages.push({ role, content, id: messageId });
    }
    
    return messageId;
}

function removeChatMessage(messageId) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) {
        messageDiv.remove();
        return true;
    }
    return false;
}

function loadChatHistory() {
    const chatMessagesDiv = document.getElementById('chat-messages');
    if (!chatMessagesDiv) {
        console.warn('Chat messages div not found');
        return;
    }
    
    // Load from localStorage first
    const storedHistory = localStorage.getItem('meetingminer_chat_history');
    if (storedHistory) {
        try {
            const parsed = JSON.parse(storedHistory);
            if (Array.isArray(parsed) && parsed.length > 0) {
                chatMessages = parsed;
                console.log('Loaded', chatMessages.length, 'messages from history');
            }
        } catch (e) {
            console.error('Error loading chat history:', e);
            chatMessages = [];
        }
    }
    
    // Clear existing messages (but keep temporary ones out)
    chatMessagesDiv.innerHTML = '';
    
    // Display all messages from history
    if (chatMessages.length > 0) {
        chatMessages.forEach((msg, index) => {
            const messageDiv = document.createElement('div');
            messageDiv.id = msg.id || 'msg-hist-' + index + '-' + Date.now();
            messageDiv.className = `chat-message ${msg.role}`;
            
            // Format content for assistant messages
            if (msg.role === 'assistant') {
                messageDiv.innerHTML = formatChatMessage(msg.content);
            } else {
                messageDiv.textContent = msg.content;
            }
            
            chatMessagesDiv.appendChild(messageDiv);
        });
        console.log('Displayed', chatMessages.length, 'messages in chat');
    } else {
        console.log('No chat history to display');
    }
    
    // Scroll to bottom
    setTimeout(() => {
        chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
    }, 100);
}

function saveChatHistory() {
    try {
        // Filter out any temporary messages before saving
        const messagesToSave = chatMessages.filter(msg => msg.content !== 'Thinking...');
        localStorage.setItem('meetingminer_chat_history', JSON.stringify(messagesToSave));
        console.log('Saved', messagesToSave.length, 'messages to history');
    } catch (e) {
        console.error('Error saving chat history:', e);
    }
}

// History
async function loadHistory() {
    const historyContent = document.getElementById('history-content');
    historyContent.innerHTML = '<div class="spinner active"></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/meetings`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayHistory(data.meetings);
        } else {
            historyContent.innerHTML = `<div class="result-message error">${data.error}</div>`;
        }
    } catch (error) {
        let errorMessage = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = `Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running.`;
        }
        historyContent.innerHTML = `<div class="result-message error">Error loading history: ${errorMessage}</div>`;
        console.error('API Error:', error);
    }
}

function displayHistory(meetings) {
    const historyContent = document.getElementById('history-content');
    
    if (meetings.length === 0) {
        historyContent.innerHTML = '<div class="info-message">No meetings processed yet.</div>';
        return;
    }
    
    historyContent.innerHTML = `
        <p><strong>Total meetings:</strong> ${meetings.length}</p>
        ${meetings.map(meeting => `
            <div class="meeting-item" onclick="viewMeeting(${meeting.id})">
                <h4>${meeting.title || 'Untitled Meeting'}</h4>
                ${meeting.project_name ? `<div style="margin-top: 6px; padding: 4px 10px; background: rgba(139, 92, 246, 0.2); border-radius: 6px; display: inline-block; border: 1px solid rgba(139, 92, 246, 0.4);">
                    <span style="color: #a78bfa; font-size: 0.9em;"><strong>Project:</strong> ${meeting.project_name}</span>
                </div>` : ''}
                <div class="date" style="margin-top: 8px;">Created: ${meeting.created_at ? new Date(meeting.created_at).toLocaleString() : 'Unknown'}</div>
            </div>
        `).join('')}
    `;
}

function viewMeeting(meetingId) {
    showPage('results');
    setTimeout(() => {
        document.getElementById('meeting-select').value = meetingId;
        loadMeetingDetails();
    }, 100);
}

// Config
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        // Could display config info if needed
        if (data.success) {
            console.log('✅ Backend connected. LLM Provider:', data.config.llm_provider);
        }
    } catch (error) {
        console.error('Error loading config:', error);
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            console.error(`⚠️ Cannot connect to backend API at ${API_BASE}. Make sure the Flask server is running on port 5000.`);
        }
    }
}

