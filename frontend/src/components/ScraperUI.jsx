import React, { useState } from 'react';
import { 
  Globe, 
  Search, 
  Download, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  Image,
  Link2,
  List,
  Table,
  AlertCircle,
  CheckCircle,
  Loader2,
  Code,
  FileJson,
  Layout
} from 'lucide-react';

const ScraperUI = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [expandedSections, setExpandedSections] = useState({});
  const [jsonView, setJsonView] = useState(false);

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
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      setResult(data.result);
    } catch (err) {
      setError(err.message || 'Failed to scrape website');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (index) => {
    setExpandedSections(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const downloadJSON = () => {
    if (!result) return;
    
    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `scrape-result-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const getSectionIcon = (type) => {
    switch(type) {
      case 'hero': return <Layout className="w-4 h-4 text-purple-400" />;
      case 'nav': return <Link2 className="w-4 h-4 text-blue-400" />;
      case 'footer': return <ChevronDown className="w-4 h-4 text-slate-400" />;
      case 'pricing': return <Table className="w-4 h-4 text-green-400" />;
      case 'faq': return <AlertCircle className="w-4 h-4 text-orange-400" />;
      case 'grid': return <Layout className="w-4 h-4 text-indigo-400" />;
      case 'list': return <List className="w-4 h-4 text-teal-400" />;
      default: return <ChevronDown className="w-4 h-4 text-slate-400" />;
    }
  };

  const renderSectionContent = (section) => {
    if (jsonView) {
      return (
        <pre className="bg-slate-950 text-slate-100 p-4 rounded-xl overflow-x-auto text-sm border border-slate-700/50">
          {JSON.stringify(section, null, 2)}
        </pre>
      );
    }

    return (
      <div className="space-y-4">
        {section.content.headings?.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <ChevronDown className="w-4 h-4" />
              Headings
            </h4>
            <ul className="space-y-2">
              {section.content.headings.map((heading, i) => (
                <li key={i} className="text-slate-200 pl-4 bg-slate-800/30 p-2 rounded-lg">• {heading}</li>
              ))}
            </ul>
          </div>
        )}

        {section.content.text && (
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3">Text Content</h4>
            <p className="text-slate-200 bg-slate-800/30 p-4 rounded-xl border border-slate-700/30">{section.content.text}</p>
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
                  className="flex items-center gap-2 text-blue-400 hover:text-blue-300 p-3 hover:bg-slate-800/50 rounded-xl transition-all duration-200 border border-slate-700/30 hover:border-slate-600/50"
                >
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate flex-1 text-slate-200">{link.text || 'No text'}</span>
                  <span className="text-xs text-slate-500 truncate max-w-xs">{link.href}</span>
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
                <div key={i} className="border border-slate-700/50 rounded-xl overflow-hidden bg-slate-900/30 hover:border-slate-600/50 transition-all duration-200">
                  <div className="bg-slate-800/50 h-32 flex items-center justify-center">
                    <Image className="w-8 h-8 text-slate-600" />
                  </div>
                  <div className="p-3">
                    <p className="text-xs text-slate-300 truncate" title={img.src}>
                      {img.src?.split('/').pop() || 'image'}
                    </p>
                    {img.alt && <p className="text-xs text-slate-500 truncate mt-1" title={img.alt}>Alt: {img.alt}</p>}
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
                  <ul className="space-y-2">
                    {list.map((item, j) => (
                      <li key={j} className="text-slate-200 flex items-start">
                        <span className="text-slate-500 mr-2">•</span>
                        <span>{item}</span>
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
            Raw HTML {section.truncated && <span className="text-xs text-orange-400">(Truncated)</span>}
          </h4>
          <pre className="bg-slate-950 text-slate-100 p-4 rounded-xl overflow-x-auto text-xs max-h-60 overflow-y-auto border border-slate-700/50">
            {section.rawHtml}
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4 md:p-8 overflow-hidden w-full">
      <div className="max-w-7xl mx-auto w-full overflow-hidden">
        {/* Header */}
        <div className="mb-12 text-center overflow-hidden">
          <div className="flex items-center justify-center gap-4 mb-4 flex-wrap">
            <div className="relative flex-shrink-0">
              <div className="absolute inset-0 bg-blue-500 blur-xl opacity-50 animate-pulse"></div>
              <Globe className="relative w-12 h-12 text-blue-400" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent break-words">
              Universal Website Scraper
            </h1>
          </div>
          <p className="text-slate-300 max-w-2xl mx-auto text-lg">
            Extract structured content, metadata, and sections from any website with precision
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Input */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl p-6 sticky top-8">
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-400" />
                Scrape Configuration
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Website URL
                  </label>
                  <div className="relative group">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-white placeholder-slate-500"
                      onKeyPress={(e) => e.key === 'Enter' && scrapeWebsite()}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
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
                      Scraping Website...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      Start Scraping
                    </>
                  )}
                </button>

                {error && (
                  <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl backdrop-blur-sm">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-red-400">Error</h4>
                        <p className="text-red-300 text-sm mt-1">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {result && (
                  <div className="pt-6 border-t border-slate-700">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-slate-200">Results</h3>
                        <button
                          onClick={() => setJsonView(!jsonView)}
                          className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                        >
                          <FileJson className="w-4 h-4" />
                          {jsonView ? 'View Content' : 'View JSON'}
                        </button>
                      </div>

                      <div className="space-y-3 bg-slate-900/30 rounded-xl p-4 border border-slate-700/50">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">Sections Found</span>
                          <span className="font-medium text-white">{result.sections?.length || 0}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">Status</span>
                          <span className="flex items-center gap-1 text-green-400">
                            <CheckCircle className="w-4 h-4" />
                            Success
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">Scraped At</span>
                          <span className="font-medium text-white">
                            {result.scrapedAt ? new Date(result.scrapedAt).toLocaleTimeString() : 'N/A'}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={downloadJSON}
                        className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2.5 px-4 rounded-xl font-medium hover:from-green-600 hover:to-emerald-600 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-green-500/20 hover:shadow-green-500/40"
                      >
                        <Download className="w-5 h-5" />
                        Download JSON
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2">
            {loading ? (
              <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl p-12 text-center">
                <div className="relative inline-block">
                  <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-30 animate-pulse"></div>
                  <Loader2 className="relative w-16 h-16 text-blue-400 animate-spin mx-auto mb-6" />
                </div>
                <h3 className="text-2xl font-semibold text-white mb-3">Scraping Website</h3>
                <p className="text-slate-400 mb-6">Fetching and parsing content from {url}</p>
                <div className="mt-8 w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full animate-pulse w-3/4 shadow-lg shadow-blue-500/50"></div>
                </div>
              </div>
            ) : result ? (
              <div className="space-y-6">
                {/* Metadata Card */}
                <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl p-6 hover:border-slate-600/50 transition-all duration-300">
                  <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    Website Metadata
                  </h2>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-700/30">
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Title</h4>
                      <p className="text-white font-medium truncate" title={result.meta?.title}>
                        {result.meta?.title || 'No title found'}
                      </p>
                    </div>
                    <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-700/30">
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Language</h4>
                      <p className="text-white font-medium">{result.meta?.language || 'en'}</p>
                    </div>
                    <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-700/30">
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Description</h4>
                      <p className="text-white line-clamp-2" title={result.meta?.description}>
                        {result.meta?.description || 'No description found'}
                      </p>
                    </div>
                    <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-700/30">
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Canonical URL</h4>
                      <a
                        href={result.meta?.canonical}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 truncate flex items-center gap-2 transition-colors"
                        title={result.meta?.canonical}
                      >
                        <ExternalLink className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate">{result.meta?.canonical || 'None'}</span>
                      </a>
                    </div>
                  </div>
                </div>

                {/* Sections Card */}
                {result.sections && result.sections.length > 0 && (
                  <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl p-6 hover:border-slate-600/50 transition-all duration-300">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                        Extracted Sections
                      </h2>
                      <span className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/30 text-blue-300 text-sm font-medium px-4 py-1.5 rounded-full">
                        {result.sections.length} sections
                      </span>
                    </div>

                    <div className="space-y-3">
                      {result.sections.map((section, index) => (
                        <div key={section.id} className="border border-slate-700/50 rounded-xl overflow-hidden hover:border-slate-600/50 transition-all duration-300">
                          <button
                            onClick={() => toggleSection(index)}
                            className="w-full p-4 bg-slate-900/30 hover:bg-slate-900/50 transition-all duration-200 flex items-center justify-between group"
                          >
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-slate-800/50 rounded-lg border border-slate-700/50 group-hover:border-slate-600/50 transition-colors">
                                {getSectionIcon(section.type)}
                              </div>
                              <div className="text-left">
                                <h3 className="font-medium text-white">{section.label}</h3>
                                <div className="flex items-center gap-3 mt-1.5">
                                  <span className="text-xs px-2.5 py-1 bg-slate-800/50 text-slate-300 rounded-lg border border-slate-700/50">
                                    {section.type}
                                  </span>
                                  <span className="text-xs text-slate-500">
                                    ID: {section.id}
                                  </span>
                                </div>
                              </div>
                            </div>
                            {expandedSections[index] ? (
                              <ChevronUp className="w-5 h-5 text-slate-400 group-hover:text-blue-400 transition-colors" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-slate-400 group-hover:text-blue-400 transition-colors" />
                            )}
                          </button>

                          {expandedSections[index] && (
                            <div className="p-4 border-t border-slate-700/50 bg-slate-900/20">
                              {renderSectionContent(section)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Errors Card (if any) */}
                {result.errors && result.errors.length > 0 && (
                  <div className="bg-red-500/10 border border-red-500/30 backdrop-blur-xl rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-red-400 mb-4 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Errors During Scraping ({result.errors.length})
                    </h3>
                    <div className="space-y-3">
                      {result.errors.map((err, index) => (
                        <div key={index} className="p-4 bg-slate-900/50 rounded-xl border border-red-500/20">
                          <div className="flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                              <h4 className="font-medium text-red-400">{err.phase}</h4>
                              <p className="text-red-300 text-sm mt-1">{err.message}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl p-12 text-center">
                <div className="relative inline-block mb-8">
                  <div className="absolute inset-0 bg-blue-500 blur-3xl opacity-20"></div>
                  <Globe className="relative w-20 h-20 text-slate-600 mx-auto" />
                </div>
                <h3 className="text-2xl font-semibold text-white mb-3">Ready to Scrape</h3>
                <p className="text-slate-400 max-w-md mx-auto mb-10">
                  Enter a website URL and click "Start Scraping" to extract structured content, metadata, and sections.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                  <div className="text-center p-6 border border-slate-700/50 rounded-xl bg-slate-900/30 hover:border-slate-600/50 transition-all duration-300 group">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-blue-600/20 text-blue-400 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Search className="w-6 h-6" />
                    </div>
                    <p className="text-sm text-slate-300 font-medium">Static Content</p>
                  </div>
                  <div className="text-center p-6 border border-slate-700/50 rounded-xl bg-slate-900/30 hover:border-slate-600/50 transition-all duration-300 group">
                    <div className="w-12 h-12 bg-gradient-to-br from-green-500/20 to-green-600/20 text-green-400 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Layout className="w-6 h-6" />
                    </div>
                    <p className="text-sm text-slate-300 font-medium">Section Detection</p>
                  </div>
                  <div className="text-center p-6 border border-slate-700/50 rounded-xl bg-slate-900/30 hover:border-slate-600/50 transition-all duration-300 group">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-purple-600/20 text-purple-400 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Download className="w-6 h-6" />
                    </div>
                    <p className="text-sm text-slate-300 font-medium">JSON Export</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-slate-700/50 text-center">
          <p className="text-slate-400 text-sm">Built with FastAPI & React for the Lyftr AI Full-Stack Assignment</p>
          <p className="mt-2 text-slate-500 text-sm">Anshuman Kumar Singh • Phase 2: Static Scraping Enhancement</p>
        </div>
      </div>
    </div>
  );
};

export default ScraperUI;