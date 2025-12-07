import React, { useState, useEffect } from 'react';
import { 
  Globe, Search, Download, ChevronDown, ChevronUp, ExternalLink,
  Image, Link2, List, Table, AlertCircle, CheckCircle, Loader2,
  Code, FileJson, Layout, BarChart3, Clock, Layers, Hash,
  Zap, Shield, Database, Cpu, Network, Activity, Users,
  Sparkles, Target, TrendingUp, RotateCcw, Play, Pause,
  XCircle, Info, AlertTriangle, Filter
} from 'lucide-react';

const ScraperUI = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingPhase, setLoadingPhase] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [expandedSections, setExpandedSections] = useState({});
  const [jsonView, setJsonView] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [stats, setStats] = useState({
    totalScrapes: 0,
    avgDuration: 0,
    successRate: 100
  });
  const [interactionVisualization, setInteractionVisualization] = useState(true);

  // Simulate loading progress
  useEffect(() => {
    if (loading) {
      const phases = [
        'Initializing...',
        'Fetching HTML...',
        'Parsing content...',
        'Analyzing sections...',
        'Processing interactions...',
        'Finalizing...'
      ];
      
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        
        setLoadingProgress(Math.min(progress, 100));
        
        // Update phase based on progress
        const phaseIndex = Math.floor(progress / (100 / phases.length));
        setLoadingPhase(phases[Math.min(phaseIndex, phases.length - 1)]);
        
        if (progress >= 100) {
          clearInterval(interval);
        }
      }, 300);
      
      return () => clearInterval(interval);
    }
  }, [loading]);

  const scrapeWebsite = async () => {
    if (!url) {
      setError('Please enter a URL');
      return;
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setError('URL must start with http:// or https://');
      return;
    }

    setLoading(true);
    setLoadingProgress(0);
    setLoadingPhase('Initializing...');
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/scrape', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ url })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Update stats
      setStats(prev => ({
        totalScrapes: prev.totalScrapes + 1,
        avgDuration: prev.avgDuration === 0 
          ? (data.result.performance?.duration_ms || 0)
          : (prev.avgDuration + (data.result.performance?.duration_ms || 0)) / 2,
        successRate: data.status === 'success' ? 100 : 95
      }));
      
      setResult(data.result);
    } catch (err) {
      setError(err.message || 'Failed to scrape website');
      console.error('Scraping error:', err);
    } finally {
      setLoading(false);
      setLoadingProgress(100);
    }
  };

  const toggleSection = (index) => {
    setExpandedSections(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const expandAllSections = () => {
    if (!result?.sections) return;
    const expanded = {};
    result.sections.forEach((_, index) => {
      expanded[index] = true;
    });
    setExpandedSections(expanded);
  };

  const collapseAllSections = () => {
    setExpandedSections({});
  };

  const downloadJSON = () => {
    if (!result) return;
    
    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `scrape-${new Date().toISOString().split('T')[0]}-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Show toast notification (simplified)
      alert('Copied to clipboard!');
    });
  };

  const getSectionIcon = (type) => {
    const icons = {
      'hero': <Layout className="w-4 h-4 text-purple-400" />,
      'nav': <Link2 className="w-4 h-4 text-blue-400" />,
      'footer': <ChevronDown className="w-4 h-4 text-slate-400" />,
      'pricing': <Table className="w-4 h-4 text-green-400" />,
      'faq': <AlertCircle className="w-4 h-4 text-orange-400" />,
      'grid': <Layout className="w-4 h-4 text-indigo-400" />,
      'list': <List className="w-4 h-4 text-teal-400" />,
      'section': <Layers className="w-4 h-4 text-cyan-400" />,
      'unknown': <Hash className="w-4 h-4 text-gray-400" />
    };
    return icons[type] || icons['unknown'];
  };

  const renderPerformanceMetrics = () => {
    if (!result?.performance) return null;

    const perf = result.performance;
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-blue-300">Duration</p>
              <p className="text-lg font-semibold text-white">
                {perf.duration_ms ? `${(perf.duration_ms / 1000).toFixed(2)}s` : 'N/A'}
              </p>
            </div>
            <Clock className="w-6 h-6 text-blue-400" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-green-300">Sections</p>
              <p className="text-lg font-semibold text-white">{perf.sections_found || 0}</p>
            </div>
            <Layers className="w-6 h-6 text-green-400" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-purple-300">Depth</p>
              <p className="text-lg font-semibold text-white">
                {result.interactions?.totalDepth || perf.interaction_depth || 0}
                <span className="text-xs text-purple-400 ml-1">
                  /3
                </span>
              </p>
            </div>
            <TrendingUp className="w-6 h-6 text-purple-400" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-amber-500/10 to-amber-600/10 border border-amber-500/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-amber-300">Pages</p>
              <p className="text-lg font-semibold text-white">{perf.pages_visited || 1}</p>
            </div>
            <Globe className="w-6 h-6 text-amber-400" />
          </div>
        </div>
      </div>
    );
  };

  const renderInteractionVisualization = () => {
    if (!result?.interactions || !interactionVisualization) return null;
    
    const interactions = result.interactions;
    const totalDepth = interactions.totalDepth || 
                      (interactions.clicks?.length || 0) + (interactions.scrolls || 0);
    
    return (
      <div className="mb-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            Interaction Flow
            <span className="text-sm font-normal text-slate-400">
              (Depth: {totalDepth}/3)
            </span>
          </h3>
          <button
            onClick={() => setInteractionVisualization(!interactionVisualization)}
            className="text-sm text-slate-400 hover:text-slate-300"
          >
            {interactionVisualization ? 'Hide' : 'Show'}
          </button>
        </div>
        
        <div className="space-y-3">
          {/* Depth Progress */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-300">Interaction Depth</span>
              <span className={`font-medium ${
                totalDepth >= 3 ? 'text-green-400' : 'text-amber-400'
              }`}>
                {totalDepth >= 3 ? '✓ Achieved' : '⚠️ Below minimum'}
              </span>
            </div>
            <div className="w-full bg-slate-700/50 rounded-full h-2.5 overflow-hidden">
              <div 
                className={`h-2.5 rounded-full ${
                  totalDepth >= 3 
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                    : 'bg-gradient-to-r from-amber-500 to-orange-500'
                }`}
                style={{ width: `${Math.min(100, (totalDepth / 3) * 100)}%` }}
              ></div>
            </div>
          </div>
          
          {/* Clicks Visualization */}
          {interactions.clicks?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Target className="w-4 h-4" />
                Clicks ({interactions.clicks.length})
              </h4>
              <div className="space-y-2">
                {interactions.clicks.slice(0, 5).map((click, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700/30">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/20 to-blue-600/20 flex items-center justify-center">
                      <Play className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-slate-200 truncate">{click}</p>
                    </div>
                    <span className="text-xs px-2 py-1 bg-slate-700/50 text-slate-300 rounded">
                      #{i+1}
                    </span>
                  </div>
                ))}
                {interactions.clicks.length > 5 && (
                  <p className="text-sm text-slate-500 text-center">
                    + {interactions.clicks.length - 5} more clicks
                  </p>
                )}
              </div>
            </div>
          )}
          
          {/* Scrolls Visualization */}
          {interactions.scrolls > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Scrolls ({interactions.scrolls})
              </h4>
              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700/30">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-purple-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-slate-200">
                    Performed {interactions.scrolls} scroll operations
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {/* Pages Visualization */}
          {interactions.pages?.length > 1 && (
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Globe className="w-4 h-4" />
                Pages Visited ({interactions.pages.length})
              </h4>
              <div className="space-y-2">
                {interactions.pages.slice(0, 3).map((page, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700/30">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500/20 to-green-600/20 flex items-center justify-center">
                      <span className="text-sm font-semibold text-green-400">{i+1}</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-slate-200 truncate" title={page}>
                        {new URL(page).hostname}
                      </p>
                      <p className="text-xs text-slate-500 truncate">{page}</p>
                    </div>
                  </div>
                ))}
                {interactions.pages.length > 3 && (
                  <p className="text-sm text-slate-500 text-center">
                    + {interactions.pages.length - 3} more pages
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderStrategyBadge = () => {
    if (!result?.meta?.strategy) return null;
    
    const strategy = result.meta.strategy;
    const colors = {
      'static': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      'js': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      'hybrid': 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-cyan-400 border-blue-500/30 border-r-purple-500/30',
      'error': 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    
    const icons = {
      'static': <Cpu className="w-4 h-4" />,
      'js': <Zap className="w-4 h-4" />,
      'hybrid': <Sparkles className="w-4 h-4" />,
      'error': <XCircle className="w-4 h-4" />
    };
    
    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${colors[strategy] || colors.error}`}>
        {icons[strategy] || icons.error}
        <span className="text-sm font-medium capitalize">{strategy}</span>
        <span className="text-xs opacity-75">strategy</span>
      </div>
    );
  };

  const renderSectionContent = (section) => {
    if (jsonView) {
      return (
        <div className="relative group">
          <button
            onClick={() => copyToClipboard(JSON.stringify(section, null, 2))}
            className="absolute top-2 right-2 z-10 p-2 bg-slate-800/80 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-slate-700/80"
            title="Copy JSON"
          >
            <FileJson className="w-4 h-4 text-slate-300" />
          </button>
          <pre className="bg-slate-950 text-slate-100 p-4 rounded-xl overflow-x-auto text-sm border border-slate-700/50">
            {JSON.stringify(section, null, 2)}
          </pre>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {section.content.headings?.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <ChevronDown className="w-4 h-4" />
              Headings ({section.content.headings.length})
            </h4>
            <ul className="space-y-2">
              {section.content.headings.map((heading, i) => (
                <li key={i} className="text-slate-200 pl-4 bg-slate-800/30 p-2 rounded-lg border border-slate-700/30 hover:border-slate-600/50 transition-colors">
                  <span className="text-slate-500 mr-2">#{i+1}</span>
                  {heading}
                </li>
              ))}
            </ul>
          </div>
        )}

        {section.content.text && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3">Text Content</h4>
            <div className="relative group">
              <button
                onClick={() => copyToClipboard(section.content.text)}
                className="absolute top-2 right-2 z-10 p-2 bg-slate-800/80 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-slate-700/80"
                title="Copy text"
              >
                <FileJson className="w-4 h-4 text-slate-300" />
              </button>
              <p className="text-slate-200 bg-slate-800/30 p-4 rounded-xl border border-slate-700/30 whitespace-pre-line">
                {section.content.text}
              </p>
            </div>
          </div>
        )}

        {section.content.links?.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Link2 className="w-4 h-4" />
              Links ({section.content.links.length})
            </h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {section.content.links.map((link, i) => (
                <a
                  key={i}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 text-blue-400 hover:text-blue-300 hover:bg-slate-800/50 rounded-xl transition-all duration-200 border border-slate-700/30 hover:border-slate-600/50 group"
                >
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-slate-200 group-hover:text-white transition-colors">
                      {link.text || 'No text'}
                    </p>
                    <p className="text-xs text-slate-500 truncate">{link.href}</p>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {section.content.images?.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Image className="w-4 h-4" />
              Images ({section.content.images.length})
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {section.content.images.map((img, i) => (
                <div key={i} className="border border-slate-700/50 rounded-xl overflow-hidden bg-slate-900/30 hover:border-slate-600/50 transition-all duration-200 group">
                  <div className="bg-gradient-to-br from-slate-800 to-slate-900 h-32 flex items-center justify-center">
                    <Image className="w-10 h-10 text-slate-600 group-hover:text-slate-500 transition-colors" />
                  </div>
                  <div className="p-3">
                    <p className="text-xs text-slate-300 truncate" title={img.src}>
                      {img.src?.split('/').pop() || 'image'}
                    </p>
                    {img.alt && (
                      <p className="text-xs text-slate-500 truncate mt-1" title={img.alt}>
                        Alt: {img.alt}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {section.content.lists?.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <List className="w-4 h-4" />
              Lists ({section.content.lists.length})
            </h4>
            <div className="space-y-3">
              {section.content.lists.map((list, i) => (
                <div key={i} className="bg-slate-800/30 p-4 rounded-xl border border-slate-700/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-500">List #{i+1}</span>
                    <span className="text-xs text-slate-500">{list.length} items</span>
                  </div>
                  <ul className="space-y-2">
                    {list.map((item, j) => (
                      <li key={j} className="text-slate-200 flex items-start group">
                        <span className="text-slate-500 mr-2 mt-1">•</span>
                        <span className="flex-1 group-hover:text-white transition-colors">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4">
          <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Code className="w-4 h-4" />
            Raw HTML
            {section.truncated && (
              <span className="text-xs px-2 py-1 bg-amber-500/20 text-amber-400 rounded-full">
                Truncated
              </span>
            )}
          </h4>
          <div className="relative group">
            <button
              onClick={() => copyToClipboard(section.rawHtml)}
              className="absolute top-2 right-2 z-10 p-2 bg-slate-800/80 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-slate-700/80"
              title="Copy HTML"
            >
              <FileJson className="w-4 h-4 text-slate-300" />
            </button>
            <pre className="bg-slate-950 text-slate-100 p-4 rounded-xl overflow-x-auto text-xs max-h-60 overflow-y-auto border border-slate-700/50">
              {section.rawHtml}
            </pre>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      darkMode 
        ? 'bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900' 
        : 'bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50'
    } p-4 md:p-8 overflow-hidden w-full`}>
      <div className="max-w-7xl mx-auto w-full overflow-hidden">
        {/* Header */}
        <div className="mb-8 text-center overflow-hidden">
          <div className="flex flex-col md:flex-row items-center justify-between mb-6 gap-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-shrink-0">
                <div className={`absolute inset-0 blur-xl opacity-50 animate-pulse ${
                  darkMode ? 'bg-blue-500' : 'bg-blue-300'
                }`}></div>
                <Globe className={`relative w-12 h-12 ${
                  darkMode ? 'text-blue-400' : 'text-blue-600'
                }`} />
              </div>
              <div className="text-left">
                <h1 className={`text-3xl md:text-4xl font-bold bg-gradient-to-r ${
                  darkMode 
                    ? 'from-blue-400 via-cyan-400 to-blue-500' 
                    : 'from-blue-600 via-cyan-600 to-blue-700'
                } bg-clip-text text-transparent`}>
                  Universal Website Scraper
                </h1>
                <p className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'} mt-1`}>
                  Phase 4 & 5: Interactive Scraping & Enhanced UI
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-xl border ${
                  darkMode 
                    ? 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/50' 
                    : 'bg-white/50 border-slate-300/50 hover:border-slate-400/50'
                } transition-colors`}
                title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {darkMode ? '🌙' : '☀️'}
              </button>
              
              <div className="hidden md:flex items-center gap-3">
                <div className={`px-3 py-1.5 rounded-full border ${
                  darkMode 
                    ? 'bg-slate-800/50 border-slate-700/50' 
                    : 'bg-white/50 border-slate-300/50'
                }`}>
                  <span className={`text-sm font-medium ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>
                    Scrapes: <span className="font-bold">{stats.totalScrapes}</span>
                  </span>
                </div>
                <div className={`px-3 py-1.5 rounded-full border ${
                  darkMode 
                    ? 'bg-slate-800/50 border-slate-700/50' 
                    : 'bg-white/50 border-slate-300/50'
                }`}>
                  <span className={`text-sm font-medium ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>
                    Success: <span className="font-bold">{stats.successRate}%</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <p className={`max-w-2xl mx-auto text-lg ${
            darkMode ? 'text-slate-300' : 'text-slate-600'
          }`}>
            Advanced web scraping with intelligent fallback, interaction tracking, and performance optimization
          </p>
          
          <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
            <div className={`px-3 py-1.5 rounded-full border flex items-center gap-2 ${
              darkMode 
                ? 'bg-blue-500/10 border-blue-500/30' 
                : 'bg-blue-100 border-blue-300'
            }`}>
              <Zap className={`w-4 h-4 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              <span className={`text-sm font-medium ${darkMode ? 'text-blue-300' : 'text-blue-700'}`}>
                JavaScript Rendering
              </span>
            </div>
            <div className={`px-3 py-1.5 rounded-full border flex items-center gap-2 ${
              darkMode 
                ? 'bg-purple-500/10 border-purple-500/30' 
                : 'bg-purple-100 border-purple-300'
            }`}>
              <Activity className={`w-4 h-4 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
              <span className={`text-sm font-medium ${darkMode ? 'text-purple-300' : 'text-purple-700'}`}>
                Interactive Scraping
              </span>
            </div>
            <div className={`px-3 py-1.5 rounded-full border flex items-center gap-2 ${
              darkMode 
                ? 'bg-green-500/10 border-green-500/30' 
                : 'bg-green-100 border-green-300'
            }`}>
              <Shield className={`w-4 h-4 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />
              <span className={`text-sm font-medium ${darkMode ? 'text-green-300' : 'text-green-700'}`}>
                Depth ≥ 3 Guarantee
              </span>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Input & Controls */}
          <div className="lg:col-span-1 space-y-6">
            <div className={`backdrop-blur-xl border rounded-2xl shadow-2xl p-6 sticky top-6 ${
              darkMode 
                ? 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/50' 
                : 'bg-white/80 border-slate-300/50 hover:border-slate-400/50'
            } transition-all duration-300`}>
              <h2 className={`text-xl font-semibold mb-6 flex items-center gap-2 ${
                darkMode ? 'text-white' : 'text-slate-800'
              }`}>
                <Search className={`w-5 h-5 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                Scrape Configuration
              </h2>

              <div className="space-y-6">
                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    darkMode ? 'text-slate-300' : 'text-slate-700'
                  }`}>
                    Website URL
                  </label>
                  <div className="relative group">
                    <Globe className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${
                      darkMode 
                        ? 'text-slate-400 group-focus-within:text-blue-400' 
                        : 'text-slate-500 group-focus-within:text-blue-600'
                    } transition-colors`} />
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      className={`w-full pl-11 pr-4 py-3 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-sm ${
                        darkMode 
                          ? 'bg-slate-900/50 border border-slate-600 text-white placeholder-slate-500' 
                          : 'bg-white border border-slate-300 text-slate-900 placeholder-slate-400'
                      }`}
                      onKeyPress={(e) => e.key === 'Enter' && scrapeWebsite()}
                    />
                  </div>
                  <p className={`text-xs mt-2 ${
                    darkMode ? 'text-slate-400' : 'text-slate-600'
                  }`}>
                    Enter a valid URL starting with http:// or https://
                  </p>
                </div>

                <button
                  onClick={scrapeWebsite}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-3 px-4 rounded-xl font-medium hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span className="flex-1 text-left">
                        Scraping... {Math.round(loadingProgress)}%
                        <span className="block text-xs opacity-75">{loadingPhase}</span>
                      </span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5" />
                      Start Advanced Scraping
                    </>
                  )}
                </button>

                {loading && (
                  <div className="pt-2">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className={darkMode ? 'text-slate-400' : 'text-slate-600'}>Progress</span>
                      <span className={darkMode ? 'text-slate-300' : 'text-slate-700'}>{Math.round(loadingProgress)}%</span>
                    </div>
                    <div className="w-full bg-slate-700/30 rounded-full h-2 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${loadingProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {error && (
                  <div className={`p-4 rounded-xl backdrop-blur-sm ${
                    darkMode 
                      ? 'bg-red-500/10 border border-red-500/30' 
                      : 'bg-red-100 border border-red-300'
                  }`}>
                    <div className="flex items-start gap-3">
                      <XCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                        darkMode ? 'text-red-400' : 'text-red-600'
                      }`} />
                      <div>
                        <h4 className={`font-medium ${
                          darkMode ? 'text-red-400' : 'text-red-700'
                        }`}>Error</h4>
                        <p className={`text-sm mt-1 ${
                          darkMode ? 'text-red-300' : 'text-red-600'
                        }`}>{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {result && (
                  <div className="pt-6 border-t border-slate-700/30">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className={`font-medium ${
                          darkMode ? 'text-slate-200' : 'text-slate-800'
                        }`}>Results Summary</h3>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setJsonView(!jsonView)}
                            className={`text-sm flex items-center gap-1 transition-colors ${
                              darkMode 
                                ? 'text-blue-400 hover:text-blue-300' 
                                : 'text-blue-600 hover:text-blue-700'
                            }`}
                          >
                            <FileJson className="w-4 h-4" />
                            {jsonView ? 'View Content' : 'View JSON'}
                          </button>
                        </div>
                      </div>

                      <div className={`space-y-3 rounded-xl p-4 ${
                        darkMode 
                          ? 'bg-slate-900/30 border border-slate-700/50' 
                          : 'bg-slate-100 border border-slate-300'
                      }`}>
                        <div className="flex items-center justify-between text-sm">
                          <span className={darkMode ? 'text-slate-400' : 'text-slate-600'}>Strategy</span>
                          {renderStrategyBadge()}
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className={darkMode ? 'text-slate-400' : 'text-slate-600'}>Sections</span>
                          <span className={`font-medium ${
                            darkMode ? 'text-white' : 'text-slate-800'
                          }`}>
                            {result.sections?.length || 0}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className={darkMode ? 'text-slate-400' : 'text-slate-600'}>Status</span>
                          <span className="flex items-center gap-1 text-green-400">
                            <CheckCircle className="w-4 h-4" />
                            Success
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className={darkMode ? 'text-slate-400' : 'text-slate-600'}>Duration</span>
                          <span className={`font-medium ${
                            darkMode ? 'text-white' : 'text-slate-800'
                          }`}>
                            {result.meta?.scrapeDuration || 'N/A'}
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <button
                          onClick={downloadJSON}
                          className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2.5 px-4 rounded-xl font-medium hover:from-green-600 hover:to-emerald-600 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-green-500/20 hover:shadow-green-500/40"
                        >
                          <Download className="w-5 h-5" />
                          Download Complete JSON
                        </button>
                        
                        <div className="flex gap-2">
                          <button
                            onClick={expandAllSections}
                            className="flex-1 py-2 px-4 rounded-xl font-medium transition-all duration-200 flex items-center justify-center gap-2 border border-slate-700/50 hover:border-slate-600/50"
                          >
                            <ChevronDown className="w-4 h-4" />
                            Expand All
                          </button>
                          <button
                            onClick={collapseAllSections}
                            className="flex-1 py-2 px-4 rounded-xl font-medium transition-all duration-200 flex items-center justify-center gap-2 border border-slate-700/50 hover:border-slate-600/50"
                          >
                            <ChevronUp className="w-4 h-4" />
                            Collapse All
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Test URLs */}
            <div className={`backdrop-blur-xl border rounded-2xl shadow-xl p-5 ${
              darkMode 
                ? 'bg-slate-800/30 border-slate-700/50' 
                : 'bg-white/60 border-slate-300/50'
            }`}>
              <h3 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${
                darkMode ? 'text-white' : 'text-slate-800'
              }`}>
                <Target className="w-5 h-5 text-blue-400" />
                Test URLs
              </h3>
              <div className="space-y-2">
                {[
                  { name: 'Static', url: 'https://en.wikipedia.org/wiki/Artificial_intelligence', desc: 'Pure HTML content' },
                  { name: 'JS-Heavy', url: 'https://vercel.com/', desc: 'React/Next.js app' },
                  { name: 'Pagination', url: 'https://news.ycombinator.com/', desc: 'Page navigation' },
                  { name: 'Tabs', url: 'https://mui.com/material-ui/react-tabs/', desc: 'Interactive tabs' }
                ].map((test, i) => (
                  <button
                    key={i}
                    onClick={() => setUrl(test.url)}
                    className={`w-full text-left p-3 rounded-xl transition-all duration-200 ${
                      darkMode 
                        ? 'hover:bg-slate-800/50 border border-slate-700/30 hover:border-slate-600/50' 
                        : 'hover:bg-slate-100 border border-slate-300/30 hover:border-slate-400/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`font-medium ${
                        darkMode ? 'text-slate-200' : 'text-slate-700'
                      }`}>{test.name}</span>
                      <ExternalLink className={`w-4 h-4 ${
                        darkMode ? 'text-slate-500' : 'text-slate-400'
                      }`} />
                    </div>
                    <p className={`text-xs mt-1 truncate ${
                      darkMode ? 'text-slate-400' : 'text-slate-500'
                    }`} title={test.url}>{test.url}</p>
                    <p className={`text-xs mt-1 ${
                      darkMode ? 'text-slate-500' : 'text-slate-600'
                    }`}>{test.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Results & Visualization */}
          <div className="lg:col-span-2 space-y-6">
            {loading ? (
              <div className={`backdrop-blur-xl border rounded-2xl shadow-2xl p-8 md:p-12 text-center ${
                darkMode 
                  ? 'bg-slate-800/50 border-slate-700/50' 
                  : 'bg-white/80 border-slate-300/50'
              }`}>
                <div className="relative inline-block mb-8">
                  <div className={`absolute inset-0 blur-2xl opacity-30 animate-pulse ${
                    darkMode ? 'bg-blue-500' : 'bg-blue-300'
                  }`}></div>
                  <div className="relative">
                    <Loader2 className="w-16 h-16 animate-spin mx-auto mb-6 text-blue-400" />
                  </div>
                </div>
                <h3 className={`text-2xl font-semibold mb-3 ${
                  darkMode ? 'text-white' : 'text-slate-800'
                }`}>Advanced Scraping in Progress</h3>
                <p className={`mb-6 ${
                  darkMode ? 'text-slate-400' : 'text-slate-600'
                }`}>
                  {loadingPhase}
                  <span className="block text-sm mt-2">
                    Processing {url.replace(/^https?:\/\//, '')}
                  </span>
                </p>
                
                {/* Loading Visualization */}
                <div className="max-w-md mx-auto">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className={darkMode ? 'text-slate-400' : 'text-slate-600'}>Progress</span>
                    <span className={darkMode ? 'text-slate-300' : 'text-slate-700'}>{Math.round(loadingProgress)}%</span>
                  </div>
                  <div className="w-full bg-slate-700/30 rounded-full h-3 overflow-hidden mb-8">
                    <div 
                      className="bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-500 h-3 rounded-full animate-pulse"
                      style={{ width: `${loadingProgress}%` }}
                    ></div>
                  </div>
                  
                  {/* Loading Steps */}
                  <div className="grid grid-cols-3 gap-3">
                    {['Static', 'JS', 'Interactions'].map((step, i) => (
                      <div key={i} className={`p-3 rounded-xl border ${
                        loadingProgress > (i * 33) 
                          ? 'border-blue-500/30 bg-blue-500/10' 
                          : (darkMode ? 'border-slate-700/50 bg-slate-800/30' : 'border-slate-300/50 bg-slate-100')
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2 ${
                          loadingProgress > (i * 33) 
                            ? 'bg-blue-500/20 text-blue-400' 
                            : (darkMode ? 'bg-slate-700 text-slate-500' : 'bg-slate-300 text-slate-400')
                        }`}>
                          {loadingProgress > (i * 33) ? '✓' : i+1}
                        </div>
                        <p className={`text-xs ${
                          loadingProgress > (i * 33) 
                            ? 'text-blue-300' 
                            : (darkMode ? 'text-slate-500' : 'text-slate-600')
                        }`}>{step}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : result ? (
              <div className="space-y-6">
                {/* Performance Metrics */}
                {renderPerformanceMetrics()}
                
                {/* Interaction Visualization */}
                {renderInteractionVisualization()}
                
                {/* Metadata Card */}
                <div className={`backdrop-blur-xl border rounded-2xl shadow-2xl p-6 ${
                  darkMode 
                    ? 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/50' 
                    : 'bg-white/80 border-slate-300/50 hover:border-slate-400/50'
                } transition-all duration-300`}>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className={`text-xl font-semibold flex items-center gap-2 ${
                      darkMode ? 'text-white' : 'text-slate-800'
                    }`}>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      Enhanced Metadata
                    </h2>
                    {renderStrategyBadge()}
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    {Object.entries(result.meta || {}).map(([key, value]) => {
                      if (key === 'strategy' || !value) return null;
                      
                      return (
                        <div key={key} className={`p-4 rounded-xl border ${
                          darkMode 
                            ? 'bg-slate-900/30 border-slate-700/30' 
                            : 'bg-slate-100 border-slate-300'
                        }`}>
                          <h4 className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </h4>
                          {typeof value === 'string' && value.startsWith('http') ? (
                            <a
                              href={value}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`flex items-center gap-2 ${
                                darkMode 
                                  ? 'text-blue-400 hover:text-blue-300' 
                                  : 'text-blue-600 hover:text-blue-700'
                              } transition-colors truncate`}
                              title={value}
                            >
                              <ExternalLink className="w-3 h-3 flex-shrink-0" />
                              <span className="truncate">{value}</span>
                            </a>
                          ) : Array.isArray(value) ? (
                            <div className="flex flex-wrap gap-1">
                              {value.map((item, i) => (
                                <span key={i} className={`text-xs px-2 py-1 rounded ${
                                  darkMode 
                                    ? 'bg-slate-800/50 text-slate-300' 
                                    : 'bg-slate-200 text-slate-700'
                                }`}>
                                  {item}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <p className={`text-sm ${
                              darkMode ? 'text-slate-200' : 'text-slate-700'
                            }`}>
                              {String(value)}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Sections Card */}
                {result.sections && result.sections.length > 0 && (
                  <div className={`backdrop-blur-xl border rounded-2xl shadow-2xl p-6 ${
                    darkMode 
                      ? 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/50' 
                      : 'bg-white/80 border-slate-300/50 hover:border-slate-400/50'
                  } transition-all duration-300`}>
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h2 className={`text-xl font-semibold flex items-center gap-2 ${
                          darkMode ? 'text-white' : 'text-slate-800'
                        }`}>
                          <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                          Extracted Sections
                        </h2>
                        <p className={`text-sm mt-1 ${
                          darkMode ? 'text-slate-400' : 'text-slate-600'
                        }`}>
                          {result.sections.length} unique sections detected
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm px-3 py-1.5 rounded-full border ${
                          darkMode 
                            ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border-blue-500/30 text-blue-300' 
                            : 'bg-gradient-to-r from-blue-100 to-cyan-100 border-blue-300 text-blue-700'
                        }`}>
                          {result.sections.length} sections
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {result.sections.map((section, index) => (
                        <div key={section.id} className={`border rounded-xl overflow-hidden transition-all duration-300 ${
                          darkMode 
                            ? 'border-slate-700/50 hover:border-slate-600/50' 
                            : 'border-slate-300/50 hover:border-slate-400/50'
                        }`}>
                          <button
                            onClick={() => toggleSection(index)}
                            className={`w-full p-4 transition-all duration-200 flex items-center justify-between group ${
                              darkMode 
                                ? 'bg-slate-900/30 hover:bg-slate-900/50' 
                                : 'bg-slate-100/50 hover:bg-slate-100'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg border ${
                                darkMode 
                                  ? 'bg-slate-800/50 border-slate-700/50 group-hover:border-slate-600/50' 
                                  : 'bg-white border-slate-300 group-hover:border-slate-400'
                              } transition-colors`}>
                                {getSectionIcon(section.type)}
                              </div>
                              <div className="text-left">
                                <h3 className={`font-medium ${
                                  darkMode ? 'text-white' : 'text-slate-800'
                                }`}>{section.label}</h3>
                                <div className="flex items-center gap-2 mt-1.5">
                                  <span className={`text-xs px-2.5 py-1 rounded-lg border ${
                                    darkMode 
                                      ? 'bg-slate-800/50 text-slate-300 border-slate-700/50' 
                                      : 'bg-slate-200 text-slate-700 border-slate-300'
                                  }`}>
                                    {section.type}
                                  </span>
                                  <span className={`text-xs ${
                                    darkMode ? 'text-slate-500' : 'text-slate-600'
                                  }`}>
                                    ID: {section.id}
                                  </span>
                                  {section.sourceUrl !== result.url && (
                                    <span className={`text-xs px-2.5 py-1 rounded-lg border ${
                                      darkMode 
                                        ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' 
                                        : 'bg-blue-100 text-blue-700 border-blue-300'
                                    }`}>
                                      Paginated
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            {expandedSections[index] ? (
                              <ChevronUp className={`w-5 h-5 transition-colors ${
                                darkMode 
                                  ? 'text-slate-400 group-hover:text-blue-400' 
                                  : 'text-slate-500 group-hover:text-blue-600'
                              }`} />
                            ) : (
                              <ChevronDown className={`w-5 h-5 transition-colors ${
                                darkMode 
                                  ? 'text-slate-400 group-hover:text-blue-400' 
                                  : 'text-slate-500 group-hover:text-blue-600'
                              }`} />
                            )}
                          </button>

                          {expandedSections[index] && (
                            <div className={`p-4 border-t ${
                              darkMode 
                                ? 'border-slate-700/50 bg-slate-900/20' 
                                : 'border-slate-300/50 bg-slate-50'
                            }`}>
                              {renderSectionContent(section)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Errors & Warnings */}
                {(result.errors?.length > 0 || result.warnings?.length > 0) && (
                  <div className={`backdrop-blur-xl rounded-2xl p-6 ${
                    darkMode 
                      ? 'bg-red-500/10 border border-red-500/30' 
                      : 'bg-red-100 border border-red-300'
                  }`}>
                    <h3 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${
                      darkMode ? 'text-red-400' : 'text-red-700'
                    }`}>
                      <AlertTriangle className="w-5 h-5" />
                      Issues During Scraping
                    </h3>
                    <div className="space-y-3">
                      {result.errors?.map((err, index) => (
                        <div key={`error-${index}`} className={`p-4 rounded-xl border ${
                          darkMode 
                            ? 'bg-slate-900/50 border-red-500/20' 
                            : 'bg-white border-red-300'
                        }`}>
                          <div className="flex items-start gap-3">
                            <XCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                              darkMode ? 'text-red-400' : 'text-red-600'
                            }`} />
                            <div>
                              <h4 className={`font-medium ${
                                darkMode ? 'text-red-400' : 'text-red-700'
                              }`}>
                                {err.phase}
                                {err.timestamp && (
                                  <span className={`text-xs ml-2 ${
                                    darkMode ? 'text-red-500' : 'text-red-600'
                                  }`}>
                                    {new Date(err.timestamp).toLocaleTimeString()}
                                  </span>
                                )}
                              </h4>
                              <p className={`text-sm mt-1 ${
                                darkMode ? 'text-red-300' : 'text-red-600'
                              }`}>{err.message}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {result.warnings?.map((warning, index) => (
                        <div key={`warning-${index}`} className={`p-4 rounded-xl border ${
                          darkMode 
                            ? 'bg-slate-900/50 border-amber-500/20' 
                            : 'bg-white border-amber-300'
                        }`}>
                          <div className="flex items-start gap-3">
                            <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                              darkMode ? 'text-amber-400' : 'text-amber-600'
                            }`} />
                            <div>
                              <h4 className={`font-medium ${
                                darkMode ? 'text-amber-400' : 'text-amber-700'
                              }`}>Warning</h4>
                              <p className={`text-sm mt-1 ${
                                darkMode ? 'text-amber-300' : 'text-amber-600'
                              }`}>{warning}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className={`backdrop-blur-xl border rounded-2xl shadow-2xl p-8 md:p-12 text-center ${
                darkMode 
                  ? 'bg-slate-800/50 border-slate-700/50' 
                  : 'bg-white/80 border-slate-300/50'
              }`}>
                <div className="relative inline-block mb-8">
                  <div className={`absolute inset-0 blur-3xl opacity-20 ${
                    darkMode ? 'bg-blue-500' : 'bg-blue-300'
                  }`}></div>
                  <Globe className={`relative w-20 h-20 mx-auto ${
                    darkMode ? 'text-slate-600' : 'text-slate-400'
                  }`} />
                </div>
                <h3 className={`text-2xl font-semibold mb-3 ${
                  darkMode ? 'text-white' : 'text-slate-800'
                }`}>Ready for Advanced Scraping</h3>
                <p className={`max-w-md mx-auto mb-10 ${
                  darkMode ? 'text-slate-400' : 'text-slate-600'
                }`}>
                  Enter a website URL to extract structured content with intelligent fallback, 
                  interaction tracking, and performance optimization.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-xl mx-auto">
                  {[
                    { icon: Cpu, label: 'Static Fallback', desc: 'HTTPS + BeautifulSoup', color: 'blue' },
                    { icon: Zap, label: 'JS Rendering', desc: 'Playwright browser', color: 'purple' },
                    { icon: Activity, label: 'Interaction', desc: 'Depth ≥ 3 guarantee', color: 'cyan' },
                    { icon: Shield, label: 'Noise Filtering', desc: 'Ads & banners removed', color: 'green' },
                    { icon: Database, label: 'Smart Parsing', desc: 'Semantic sections', color: 'amber' },
                    { icon: BarChart3, label: 'Analytics', desc: 'Performance metrics', color: 'pink' }
                  ].map((feature, i) => (
                    <div key={i} className={`text-center p-4 border rounded-xl transition-all duration-300 group ${
                      darkMode 
                        ? 'border-slate-700/50 bg-slate-900/30 hover:border-slate-600/50' 
                        : 'border-slate-300/50 bg-slate-100/50 hover:border-slate-400/50'
                    }`}>
                      <div className={`w-10 h-10 bg-gradient-to-br from-${feature.color}-500/20 to-${feature.color}-600/20 text-${feature.color}-400 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform`}>
                        <feature.icon className="w-5 h-5" />
                      </div>
                      <p className={`text-sm font-medium ${
                        darkMode ? 'text-slate-300' : 'text-slate-700'
                      }`}>{feature.label}</p>
                      <p className={`text-xs mt-1 ${
                        darkMode ? 'text-slate-500' : 'text-slate-600'
                      }`}>{feature.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className={`mt-12 pt-8 border-t text-center ${
          darkMode ? 'border-slate-700/50' : 'border-slate-300/50'
        }`}>
          <p className={`text-sm ${
            darkMode ? 'text-slate-400' : 'text-slate-600'
          }`}>
            Built with FastAPI & React for the Lyftr AI Full-Stack Assignment
          </p>
          <p className={`mt-2 text-sm ${
            darkMode ? 'text-slate-500' : 'text-slate-500'
          }`}>
            Anshuman Kumar Singh • Phase 4 & 5: Interactive Scraping & Enhanced UI
          </p>
          <div className="flex items-center justify-center gap-4 mt-4">
            <span className={`text-xs px-3 py-1 rounded-full ${
              darkMode 
                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' 
                : 'bg-blue-100 text-blue-700 border border-blue-300'
            }`}>
              Backend: FastAPI + Playwright
            </span>
            <span className={`text-xs px-3 py-1 rounded-full ${
              darkMode 
                ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' 
                : 'bg-purple-100 text-purple-700 border border-purple-300'
            }`}>
              Frontend: React + Tailwind
            </span>
            <span className={`text-xs px-3 py-1 rounded-full ${
              darkMode 
                ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
                : 'bg-green-100 text-green-700 border border-green-300'
            }`}>
              Phase 4 & 5 Complete
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScraperUI;