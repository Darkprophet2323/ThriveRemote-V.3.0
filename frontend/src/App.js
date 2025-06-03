import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const App = () => {
  const [activeWindows, setActiveWindows] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [savings, setSavings] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Window management
  const openWindow = (windowId, title, component) => {
    if (!activeWindows.find(w => w.id === windowId)) {
      setActiveWindows([...activeWindows, {
        id: windowId,
        title,
        component,
        minimized: false,
        position: { x: 50 + (activeWindows.length * 30), y: 50 + (activeWindows.length * 30) }
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

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobsRes, appsRes, savingsRes, tasksRes, statsRes] = await Promise.all([
          fetch(`${BACKEND_URL}/api/jobs`),
          fetch(`${BACKEND_URL}/api/applications`),
          fetch(`${BACKEND_URL}/api/savings`),
          fetch(`${BACKEND_URL}/api/tasks`),
          fetch(`${BACKEND_URL}/api/dashboard/stats`)
        ]);

        setJobs((await jobsRes.json()).jobs);
        setApplications((await appsRes.json()).applications);
        setSavings(await savingsRes.json());
        setTasks((await tasksRes.json()).tasks);
        setDashboardStats(await statsRes.json());
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    
    // Update time every second
    const timeInterval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timeInterval);
  }, []);

  // Desktop Applications
  const applications_list = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊', component: 'Dashboard' },
    { id: 'jobs', name: 'Job Search', icon: '💼', component: 'JobSearch' },
    { id: 'savings', name: 'Savings Goal', icon: '💰', component: 'SavingsTracker' },
    { id: 'tasks', name: 'Task Manager', icon: '✅', component: 'TaskManager' },
    { id: 'terminal', name: 'Terminal', icon: '⚡', component: 'Terminal' },
    { id: 'skills', name: 'Skills', icon: '🎓', component: 'SkillDev' }
  ];

  // Window Components
  const Dashboard = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> overview --stats
      </div>
      {dashboardStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className="stat-card">
            <div className="stat-value">{dashboardStats.total_applications}</div>
            <div className="stat-label">Applications</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{dashboardStats.interviews_scheduled}</div>
            <div className="stat-label">Interviews</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{dashboardStats.savings_progress}%</div>
            <div className="stat-label">Savings Goal</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{dashboardStats.tasks_completed_today}</div>
            <div className="stat-label">Tasks Today</div>
          </div>
        </div>
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
      </div>
    </div>
  );

  const JobSearch = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> jobs --list --remote
      </div>
      <div className="space-y-3 mt-4 max-h-96 overflow-y-auto">
        {jobs.map((job, index) => (
          <div key={job.id} className="job-card">
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
                  <button className="apply-btn mt-2">Apply Now</button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const SavingsTracker = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> savings --progress --goal=5000
      </div>
      {savings && (
        <div className="mt-4">
          <div className="savings-progress-container">
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
              {savings.progress_percentage}% Complete
            </div>
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
              <h4 className="text-white font-bold mb-3">Monthly Progress</h4>
              <div className="space-y-2">
                {savings.monthly_progress.map((month, index) => (
                  <div key={index} className="flex justify-between items-center bg-gray-800 p-2 rounded">
                    <span className="text-gray-300">{month.month}</span>
                    <span className="text-green-400 font-bold">${month.amount}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const TaskManager = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> tasks --status --priority
      </div>
      <div className="space-y-3 mt-4 max-h-96 overflow-y-auto">
        {tasks.map((task, index) => (
          <div key={task.id} className="task-card">
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

  const Terminal = () => {
    const [terminalInput, setTerminalInput] = useState('');
    const [terminalHistory, setTerminalHistory] = useState([
      'ThriveRemote Terminal v1.0 - Remote Work Command Center',
      'Type "help" for available commands',
      ''
    ]);

    const handleTerminalCommand = (e) => {
      if (e.key === 'Enter') {
        const command = terminalInput.trim();
        const newHistory = [...terminalHistory, `thriveremote@system:~$ ${command}`];
        
        switch (command.toLowerCase()) {
          case 'help':
            newHistory.push('Available commands:', 'jobs - List remote jobs', 'savings - Show savings progress', 'tasks - List active tasks', 'clear - Clear terminal');
            break;
          case 'jobs':
            newHistory.push(`Found ${jobs.length} remote job opportunities`);
            break;
          case 'savings':
            newHistory.push(`Savings: $${savings?.current_amount || 0} / $5000 (${savings?.progress_percentage || 0}%)`);
            break;
          case 'tasks':
            newHistory.push(`Active tasks: ${tasks.filter(t => t.status !== 'completed').length}`);
            break;
          case 'clear':
            setTerminalHistory(['Terminal cleared']);
            break;
          default:
            newHistory.push(`Command not found: ${command}`);
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
            placeholder="Enter command..."
            autoFocus
          />
        </div>
      </div>
    );
  };

  const SkillDev = () => (
    <div className="terminal-content">
      <div className="terminal-header">
        <span className="text-cyan-400">thriveremote@system:~$</span> skills --progress --development
      </div>
      <div className="space-y-4 mt-4">
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>React Development</span>
            <span>Advanced</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '85%' }}></div>
          </div>
        </div>
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>Python/FastAPI</span>
            <span>Intermediate</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '70%' }}></div>
          </div>
        </div>
        <div className="skill-progress">
          <div className="flex justify-between text-white mb-1">
            <span>Kubernetes</span>
            <span>Learning</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: '40%' }}></div>
          </div>
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
      default: return <div>Unknown component</div>;
    }
  };

  return (
    <div className="os-desktop">
      {/* Desktop Background */}
      <div className="desktop-bg"></div>
      
      {/* Top Panel */}
      <div className="top-panel">
        <div className="flex items-center">
          <div className="os-logo">ThriveRemote OS</div>
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
        {applications_list.map(app => (
          <div
            key={app.id}
            className="desktop-app"
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
            top: window.position.y
          }}
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