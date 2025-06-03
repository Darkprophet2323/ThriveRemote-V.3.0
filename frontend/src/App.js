import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const USER_ID = 'default_user'; // In production, this would come from authentication

const App = () => {
  const [activeWindows, setActiveWindows] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [savings, setSavings] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [konamiSequence, setKonamiSequence] = useState([]);
  const [dragging, setDragging] = useState(null);

  // Konami code sequence
  const KONAMI_CODE = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];

  // Handle Konami code
  useEffect(() => {
    const handleKeyDown = (e) => {
      setKonamiSequence(prev => {
        const newSequence = [...prev, e.code].slice(-10);
        if (JSON.stringify(newSequence) === JSON.stringify(KONAMI_CODE)) {
          triggerKonamiEasterEgg();
          return [];
        }
        return newSequence;
      });
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const triggerKonamiEasterEgg = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/terminal/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'konami', user_id: USER_ID })
      });
      const result = await response.json();
      
      setNotifications(prev => [...prev, {
        id: 'konami',
        type: 'achievement',
        title: '🎮 Konami Code!',
        message: 'Productivity boost activated! +50 points',
        timestamp: new Date().toISOString()
      }]);
      
      // Fun visual effect
      document.body.style.animation = 'rainbow 2s ease-in-out';
      setTimeout(() => {
        document.body.style.animation = '';
      }, 2000);
      
      console.log('Konami code activated!', result);
    } catch (error) {
      console.error('Konami easter egg failed:', error);
    }
  };

  // Window management with drag support
  const openWindow = (windowId, title, component) => {
    if (!activeWindows.find(w => w.id === windowId)) {
      setActiveWindows([...activeWindows, {
        id: windowId,
        title,
        component,
        minimized: false,
        position: { x: 50 + (activeWindows.length * 30), y: 50 + (activeWindows.length * 30) },
        zIndex: 1000 + activeWindows.length
      }]);
    }
  };

  const closeWindow = (windowId) => {
    setActiveWindows(activeWindows.filter(w => w.id !== windowId));
  };

  const minimizeWindow = (windowId) => {
    setActiveWindows(activeWindows.map(w => 
      w.id === windowId ? { ...w, minimized: !w.minimized } : w
    ));
  };

  const bringToFront = (windowId) => {
    const maxZ = Math.max(...activeWindows.map(w => w.zIndex), 1000);
    setActiveWindows(activeWindows.map(w => 
      w.id === windowId ? { ...w, zIndex: maxZ + 1 } : w
    ));
  };

  // Drag functionality
  const handleMouseDown = (e, windowId) => {
    if (e.target.classList.contains('window-header') || e.target.classList.contains('window-title')) {
      const window = activeWindows.find(w => w.id === windowId);
      setDragging({
        windowId,
        startX: e.clientX - window.position.x,
        startY: e.clientY - window.position.y
      });
      bringToFront(windowId);
    }
  };

  const handleMouseMove = useCallback((e) => {
    if (dragging) {
      setActiveWindows(windows => windows.map(w => 
        w.id === dragging.windowId 
          ? { ...w, position: { x: e.clientX - dragging.startX, y: e.clientY - dragging.startY } }
          : w
      ));
    }
  }, [dragging]);

  const handleMouseUp = () => {
    setDragging(null);
  };

  useEffect(() => {
    if (dragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [dragging, handleMouseMove]);

  // Fetch data and setup real-time updates
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobsRes, appsRes, savingsRes, tasksRes, statsRes, achievementsRes, notificationsRes] = await Promise.all([
          fetch(`${BACKEND_URL}/api/jobs?user_id=${USER_ID}`),
          fetch(`${BACKEND_URL}/api/applications?user_id=${USER_ID}`),
          fetch(`${BACKEND_URL}/api/savings?user_id=${USER_ID}`),
          fetch(`${BACKEND_URL}/api/tasks?user_id=${USER_ID}`),
          fetch(`${BACKEND_URL}/api/dashboard/stats?user_id=${USER_ID}`),
          fetch(`${BACKEND_URL}/api/achievements?user_id=${USER_ID}`),
          fetch(`${BACKEND_URL}/api/realtime/notifications?user_id=${USER_ID}`)
        ]);

        setJobs((await jobsRes.json()).jobs);
        setApplications((await appsRes.json()).applications);
        setSavings(await savingsRes.json());
        setTasks((await tasksRes.json()).tasks);
        setDashboardStats(await statsRes.json());
        setAchievements((await achievementsRes.json()).achievements);
        setNotifications((await notificationsRes.json()).notifications);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    
    // Real-time updates every 30 seconds
    const dataInterval = setInterval(fetchData, 30000);
    
    // Update time every second
    const timeInterval = setInterval(() => setCurrentTime(new Date()), 1000);
    
    return () => {
      clearInterval(dataInterval);
      clearInterval(timeInterval);
    };
  }, []);

  // Desktop Applications (Enhanced)
  const applications_list = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊', component: 'Dashboard' },
    { id: 'jobs', name: 'Job Search', icon: '💼', component: 'JobSearch' },
    { id: 'savings', name: 'Savings Goal', icon: '💰', component: 'SavingsTracker' },
    { id: 'tasks', name: 'Task Manager', icon: '✅', component: 'TaskManager' },
    { id: 'terminal', name: 'Terminal', icon: '⚡', component: 'Terminal' },
    { id: 'skills', name: 'Skills', icon: '🎓', component: 'SkillDev' },
    { id: 'pong', name: 'Pong Game', icon: '🎮', component: 'PongGame' },
    { id: 'achievements', name: 'Achievements', icon: '🏆', component: 'Achievements' }
  ];

  // Notification system
  const dismissNotification = (notificationId) => {
    setNotifications(notifications.filter(n => n.id !== notificationId));
  };

  // Auto-dismiss notifications after 5 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setNotifications(prev => prev.filter(n => {
        const age = new Date() - new Date(n.timestamp);
        return age < 5000; // 5 seconds
      }));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Window Components
  const Dashboard = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> dashboard --stats --realtime
      </div>
      {dashboardStats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="stat-card pulse-glow">
              <div className="stat-value">{dashboardStats.total_applications}</div>
              <div className="stat-label">Applications</div>
            </div>
            <div className="stat-card pulse-glow">
              <div className="stat-value">{dashboardStats.interviews_scheduled}</div>
              <div className="stat-label">Interviews</div>
            </div>
            <div className="stat-card pulse-glow">
              <div className="stat-value">{dashboardStats.savings_progress.toFixed(1)}%</div>
              <div className="stat-label">Savings Goal</div>
            </div>
            <div className="stat-card pulse-glow">
              <div className="stat-value">{dashboardStats.tasks_completed_today}</div>
              <div className="stat-label">Tasks Today</div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="stat-card achievement-glow">
              <div className="stat-value text-orange-400">{dashboardStats.daily_streak}</div>
              <div className="stat-label">🔥 Daily Streak</div>
            </div>
            <div className="stat-card achievement-glow">
              <div className="stat-value text-purple-400">{dashboardStats.productivity_score}</div>
              <div className="stat-label">📈 Productivity</div>
            </div>
            <div className="stat-card achievement-glow">
              <div className="stat-value text-yellow-400">{dashboardStats.achievements_unlocked}/6</div>
              <div className="stat-label">🏆 Achievements</div>
            </div>
            <div className="stat-card achievement-glow">
              <div className="stat-value text-green-400">{dashboardStats.pong_high_score}</div>
              <div className="stat-label">🎮 Pong Score</div>
            </div>
          </div>
        </>
      )}
      
      <div className="mt-6">
        <div className="terminal-line">
          <span className="text-green-400">●</span> System Status: OPTIMAL
        </div>
        <div className="terminal-line">
          <span className="text-blue-400">●</span> Remote Jobs Monitored: {dashboardStats?.active_jobs_watching || 0}
        </div>
        <div className="terminal-line">
          <span className="text-purple-400">●</span> Skill Development: {dashboardStats?.skill_development_hours || 0}h
        </div>
        <div className="terminal-line">
          <span className="text-orange-400">🔥</span> Streak Bonus: ${savings?.streak_bonus || 0}
        </div>
      </div>
    </div>
  );

  const JobSearch = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> jobs --list --remote --hot
      </div>
      <div className="space-y-3 mt-4 max-h-96 overflow-y-auto">
        {jobs.map((job, index) => (
          <div key={job.id} className="job-card fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-white font-bold">{job.title}</h3>
                <p className="text-gray-300">{job.company} • {job.location}</p>
                <p className="text-green-400 font-semibold">{job.salary}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {job.skills.map(skill => (
                    <span key={skill} className="skill-tag">{skill}</span>
                  ))}
                </div>
              </div>
              <div className="text-right">
                <span className={`status-badge ${job.application_status === 'applied' ? 'applied' : 
                  job.application_status === 'interviewing' ? 'interviewing' : 'not-applied'}`}>
                  {job.application_status.replace('_', ' ')}
                </span>
                {job.application_status === 'not_applied' && (
                  <button 
                    className="apply-btn mt-2"
                    onClick={() => applyToJob(job.id)}
                  >
                    Apply Now ⚡
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const applyToJob = async (jobId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/jobs/${jobId}/apply?user_id=${USER_ID}`, {
        method: 'POST'
      });
      const result = await response.json();
      
      setNotifications(prev => [...prev, {
        id: `apply_${jobId}`,
        type: 'success',
        title: '🎯 Application Sent!',
        message: `${result.message} (+${result.points_earned} points)`,
        timestamp: new Date().toISOString()
      }]);
      
      // Update jobs state
      setJobs(jobs.map(job => 
        job.id === jobId ? { ...job, application_status: 'applied' } : job
      ));
      
      // Refresh data to show updated stats
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      console.error('Error applying to job:', error);
    }
  };

  const SavingsTracker = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> savings --progress --goal=5000 --streak
      </div>
      {savings && (
        <div className="mt-4">
          <div className="savings-progress-container achievement-glow">
            <div className="flex justify-between text-white mb-2">
              <span>Progress to $5,000 Goal</span>
              <span>${savings.current_amount.toFixed(2)}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${savings.progress_percentage}%` }}
              ></div>
            </div>
            <div className="text-center mt-2 text-green-400 font-bold">
              {savings.progress_percentage.toFixed(1)}% Complete
            </div>
            {savings.streak_bonus > 0 && (
              <div className="text-center mt-1 text-orange-400 text-sm">
                🔥 Streak Bonus: +${savings.streak_bonus}
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="stat-card">
              <div className="stat-value">${savings.monthly_target}</div>
              <div className="stat-label">Monthly Target</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{savings.months_to_goal}</div>
              <div className="stat-label">Months to Goal</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">${(5000 - savings.current_amount).toFixed(0)}</div>
              <div className="stat-label">Remaining</div>
            </div>
          </div>

          {savings.monthly_progress && (
            <div className="mt-6">
              <h4 className="text-white font-bold mb-3">Monthly Progress 📈</h4>
              <div className="space-y-2">
                {savings.monthly_progress.map((month, index) => (
                  <div key={index} className="flex justify-between items-center bg-gray-800 p-2 rounded">
                    <span className="text-gray-300">{month.month}</span>
                    <div className="text-right">
                      <span className="text-green-400 font-bold">${month.amount}</span>
                      {month.streak_days && (
                        <div className="text-orange-400 text-xs">🔥 {month.streak_days} days</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const TaskManager = () => {
    const handleFileUpload = async (event) => {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch(`${BACKEND_URL}/api/tasks/upload`, {
          method: 'POST',
          body: formData
        });
        const result = await response.json();
        
        setNotifications(prev => [...prev, {
          id: 'task_upload',
          type: 'success',
          title: '📋 Tasks Uploaded!',
          message: result.message,
          timestamp: new Date().toISOString()
        }]);
      } catch (error) {
        console.error('Error uploading tasks:', error);
      }
    };

    const downloadTasks = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/tasks/download`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'thriveremote_tasks.json';
        a.click();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Error downloading tasks:', error);
      }
    };

    return (
      <div className="terminal-content">
        <div className="terminal-header">
          <span className="text-cyan-400">thriveremote@system:~$</span> tasks --status --priority --import/export
        </div>
        
        <div className="flex gap-2 mb-4">
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
            id="task-upload"
          />
          <label htmlFor="task-upload" className="apply-btn cursor-pointer">
            📤 Upload Tasks
          </label>
          <button onClick={downloadTasks} className="apply-btn">
            📥 Download Tasks
          </button>
        </div>

        <div className="space-y-3 mt-4 max-h-96 overflow-y-auto">
          {tasks.map((task, index) => (
            <div key={task.id} className="task-card fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-white font-semibold">{task.title}</h4>
                  <p className="text-gray-300 text-sm">{task.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`priority-badge ${task.priority}`}>{task.priority}</span>
                    <span className="category-badge">{task.category}</span>
                    {task.due_date && (
                      <span className="text-yellow-400 text-xs">Due: {task.due_date}</span>
                    )}
                  </div>
                </div>
                <span className={`status-badge ${task.status.replace('_', '-')}`}>
                  {task.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const Terminal = () => {
    const [terminalInput, setTerminalInput] = useState('');
    const [terminalHistory, setTerminalHistory] = useState([
      'ThriveRemote Terminal v2.0 - Remote Work Command Center 🚀',
      'Enhanced with Easter Eggs, Real-time Stats & Productivity Boosters!',
      'Type "help" for available commands',
      ''
    ]);

    const handleTerminalCommand = async (e) => {
      if (e.key === 'Enter' && terminalInput.trim()) {
        const command = terminalInput.trim();
        const newHistory = [...terminalHistory, `thriveremote@system:~$ ${command}`];
        
        try {
          const response = await fetch(`${BACKEND_URL}/api/terminal/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.output && Array.isArray(result.output)) {
              newHistory.push(...result.output);
            } else {
              newHistory.push('Command executed successfully');
            }
          } else {
            newHistory.push(`Server error: ${response.status}`);
          }
        } catch (error) {
          newHistory.push(`Network error: Unable to connect to server`);
          console.error('Terminal command error:', error);
        }
        
        setTerminalHistory(newHistory);
        setTerminalInput('');
      }
    };

    return (
      <div className="terminal-content">
        <div className="terminal-output space-y-1 mb-4 max-h-64 overflow-y-auto">
          {terminalHistory.map((line, index) => (
            <div key={index} className="terminal-line">{line}</div>
          ))}
        </div>
        <div className="terminal-input-line">
          <span className="text-cyan-400">thriveremote@system:~$</span>
          <input
            type="text"
            value={terminalInput}
            onChange={(e) => setTerminalInput(e.target.value)}
            onKeyDown={handleTerminalCommand}
            className="terminal-input ml-2 flex-1"
            placeholder="Enter command... (try 'help', 'surprise', or 'konami')"
            autoFocus
          />
        </div>
      </div>
    );
  };

  const PongGame = () => {
    const [gameScore, setGameScore] = useState(0);
    const [ballPos, setBallPos] = useState({ x: 50, y: 50 });
    const [ballVel, setBallVel] = useState({ x: 2, y: 2 });
    const [paddlePos, setPaddlePos] = useState(40);
    const [gameRunning, setGameRunning] = useState(false);
    const [highScore, setHighScore] = useState(dashboardStats?.pong_high_score || 0);

    useEffect(() => {
      if (!gameRunning) return;

      const gameLoop = setInterval(() => {
        setBallPos(prev => {
          let newX = prev.x + ballVel.x;
          let newY = prev.y + ballVel.y;
          let newVelX = ballVel.x;
          let newVelY = ballVel.y;

          // Wall collisions
          if (newX <= 0 || newX >= 100) newVelX = -newVelX;
          if (newY <= 0) newVelY = -newVelY;

          // Paddle collision
          if (newY >= 90 && newX >= paddlePos - 5 && newX <= paddlePos + 15) {
            newVelY = -Math.abs(newVelY);
            setGameScore(prev => prev + 10);
          }

          // Game over
          if (newY >= 100) {
            setGameRunning(false);
            updateHighScore(gameScore);
            return prev;
          }

          setBallVel({ x: newVelX, y: newVelY });
          return { x: newX, y: newY };
        });
      }, 50);

      return () => clearInterval(gameLoop);
    }, [gameRunning, ballVel, paddlePos, gameScore]);

    const updateHighScore = async (score) => {
      if (score > highScore) {
        setHighScore(score);
        try {
          const response = await fetch(`${BACKEND_URL}/api/pong/score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ score })
          });
          const result = await response.json();
          
          setNotifications(prev => [...prev, {
            id: 'pong_score',
            type: 'achievement',
            title: result.message,
            message: `Score: ${score}`,
            timestamp: new Date().toISOString()
          }]);
        } catch (error) {
          console.error('Error updating score:', error);
        }
      }
    };

    const startGame = () => {
      setGameScore(0);
      setBallPos({ x: 50, y: 20 });
      setBallVel({ x: 2, y: 2 });
      setPaddlePos(40);
      setGameRunning(true);
    };

    const movePaddle = (e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      setPaddlePos(Math.max(10, Math.min(80, x)));
    };

    return (
      <div className="terminal-content">
        <div className="terminal-header">
          <span className="text-cyan-400">thriveremote@system:~$</span> pong --retro --addictive
        </div>
        
        <div className="text-center mb-4">
          <div className="text-white">Score: {gameScore} | High Score: {highScore}</div>
          {!gameRunning && (
            <button onClick={startGame} className="apply-btn mt-2">
              {gameScore === 0 ? 'Start Game 🎮' : 'Play Again 🎮'}
            </button>
          )}
        </div>

        <div 
          className="pong-game"
          onMouseMove={movePaddle}
          style={{ cursor: gameRunning ? 'none' : 'pointer' }}
        >
          <div 
            className="pong-ball"
            style={{ 
              left: `${ballPos.x}%`, 
              top: `${ballPos.y}%`,
              opacity: gameRunning ? 1 : 0.5
            }}
          />
          <div 
            className="pong-paddle"
            style={{ left: `${paddlePos}%` }}
          />
        </div>

        <div className="text-center text-gray-400 text-sm mt-2">
          {gameRunning ? 'Move mouse to control paddle!' : 'Click Start Game to begin!'}
        </div>
      </div>
    );
  };

  const Achievements = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> achievements --list --progress
      </div>
      <div className="space-y-3 mt-4 max-h-96 overflow-y-auto">
        {achievements.map((achievement, index) => (
          <div 
            key={achievement.id} 
            className={`achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'} fade-in-up`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-center gap-4">
              <div className="text-4xl">{achievement.icon}</div>
              <div className="flex-1">
                <h4 className="text-white font-bold">{achievement.title}</h4>
                <p className="text-gray-300 text-sm">{achievement.description}</p>
                {achievement.unlocked && achievement.unlock_date && (
                  <p className="text-green-400 text-xs">
                    Unlocked: {new Date(achievement.unlock_date).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className={`achievement-status ${achievement.unlocked ? 'unlocked' : 'locked'}`}>
                {achievement.unlocked ? '✓' : '🔒'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const SkillDev = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> skills --progress --development --gamified
      </div>
      <div className="space-y-4 mt-4">
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>React Development</span>
            <span>Advanced (85%)</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '85%' }}></div>
          </div>
          <div className="text-xs text-gray-400 mt-1">Next: React 18 Concurrent Features</div>
        </div>
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>Python/FastAPI</span>
            <span>Intermediate (70%)</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '70%' }}></div>
          </div>
          <div className="text-xs text-gray-400 mt-1">Next: Advanced Database Design</div>
        </div>
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>Kubernetes</span>
            <span>Learning (40%)</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '40%' }}></div>
          </div>
          <div className="text-xs text-gray-400 mt-1">Next: Service Mesh Concepts</div>
        </div>
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>System Design</span>
            <span>Beginner (25%)</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '25%' }}></div>
          </div>
          <div className="text-xs text-gray-400 mt-1">Next: Load Balancing Strategies</div>
        </div>
      </div>
    </div>
  );

  const renderWindowContent = (component) => {
    switch (component) {
      case 'Dashboard': return <Dashboard />;
      case 'JobSearch': return <JobSearch />;
      case 'SavingsTracker': return <SavingsTracker />;
      case 'TaskManager': return <TaskManager />;
      case 'Terminal': return <Terminal />;
      case 'SkillDev': return <SkillDev />;
      case 'PongGame': return <PongGame />;
      case 'Achievements': return <Achievements />;
      default: return <div>Unknown component</div>;
    }
  };

  return (
    <div className="os-desktop">
      {/* Desktop Background */}
      <div className="desktop-bg"></div>
      
      {/* Notification System */}
      <div className="notification-container">
        {notifications.map(notification => (
          <div 
            key={notification.id} 
            className={`notification ${notification.type} slide-in`}
            onClick={() => dismissNotification(notification.id)}
          >
            <div className="notification-title">{notification.title}</div>
            <div className="notification-message">{notification.message}</div>
          </div>
        ))}
      </div>
      
      {/* Top Panel */}
      <div className="top-panel">
        <div className="flex items-center">
          <div className="os-logo">ThriveRemote OS v2.0</div>
          <div className="ml-4 text-xs text-green-400">
            🔥 {dashboardStats?.daily_streak || 0} day streak | 📈 {dashboardStats?.productivity_score || 0}/100
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <div className="system-stats">
              CPU: 15% | RAM: 8.2GB | NET: ↑2.1MB ↓1.4MB
            </div>
            <div className="system-time">
              {currentTime.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Desktop Applications Grid */}
      <div className="desktop-apps">
        {applications_list.map((app, index) => (
          <div
            key={app.id}
            className="desktop-app fade-in-up"
            style={{ animationDelay: `${index * 0.1}s` }}
            onClick={() => openWindow(app.id, app.name, app.component)}
          >
            <div className="app-icon">{app.icon}</div>
            <div className="app-name">{app.name}</div>
          </div>
        ))}
      </div>

      {/* Active Windows */}
      {activeWindows.map(window => (
        <div
          key={window.id}
          className={`window ${window.minimized ? 'minimized' : ''}`}
          style={{
            left: window.position.x,
            top: window.position.y,
            zIndex: window.zIndex
          }}
          onMouseDown={(e) => handleMouseDown(e, window.id)}
        >
          <div className="window-header">
            <div className="window-title">{window.title}</div>
            <div className="window-controls">
              <button
                className="window-control minimize"
                onClick={() => minimizeWindow(window.id)}
              >
                −
              </button>
              <button
                className="window-control close"
                onClick={() => closeWindow(window.id)}
              >
                ×
              </button>
            </div>
          </div>
          {!window.minimized && (
            <div className="window-content">
              {renderWindowContent(window.component)}
            </div>
          )}
        </div>
      ))}

      {/* Taskbar */}
      <div className="taskbar">
        <div className="taskbar-left">
          <div className="start-menu">
            <span className="text-cyan-400">⚡</span> ThriveRemote
          </div>
        </div>
        <div className="taskbar-center">
          {activeWindows.map(window => (
            <div
              key={window.id}
              className={`taskbar-item ${window.minimized ? 'minimized' : ''}`}
              onClick={() => minimizeWindow(window.id)}
            >
              {window.title}
            </div>
          ))}
        </div>
        <div className="taskbar-right">
          <div className="system-tray">
            <span className="text-green-400">●</span> Online
            <span className="ml-2">{currentTime.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;