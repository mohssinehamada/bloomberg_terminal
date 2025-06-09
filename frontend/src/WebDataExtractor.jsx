import { useState } from 'react';
import axios from 'axios';
import { Globe, Settings, AlertTriangle, Check, RefreshCcw, ChevronDown, ChevronUp, HelpCircle, Info, ArrowRight } from 'lucide-react';

export default function WebDataExtractor() {
  const [url, setUrl] = useState('');
  const [taskType, setTaskType] = useState('Interest Rate Extraction');
  const [location, setLocation] = useState('');
  const [additionalInstructions, setAdditionalInstructions] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('extraction');
  const [showTips, setShowTips] = useState(true);
  const [executionSteps, setExecutionSteps] = useState([]);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsRunning(true);
    setProgress(0);
    setResult(null);
    setError(null);
    setExecutionSteps([]);

    // Simulated progress steps
    const steps = [
      { message: '🚀 Initializing browser agent...', time: 1000 },
      { message: '🌐 Launching browser and navigating to URL...', time: 2000 },
      { message: '🔍 Analyzing webpage structure...', time: 3000 },
      { message: '⚙️ Executing data extraction task...', time: 4000 },
      { message: '📊 Processing extracted data...', time: 2000 },
      { message: '✅ Task completed successfully', time: 1000 },
    ];

    let currentProgress = 0;

    // Simulate progress for UI
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      await new Promise(resolve => setTimeout(resolve, step.time));
      setExecutionSteps(prevSteps => [...prevSteps, step.message]);
      currentProgress = (i + 1) / steps.length;
      setProgress(currentProgress);
    }

    try {
      // Map task type to backend-compatible format
      const taskTypeMap = {
        'Interest Rate Extraction': 'interest_rate',
        'Real Estate Listings': 'real_estate',
      };

      // Send request to backend
      const response = await axios.post('http://localhost:8000/extract', {
        website_url: url,
        task_type: taskTypeMap[taskType],
        location: taskType === 'Real Estate Listings' ? location : null,
        additional_instructions: additionalInstructions || null,
      });

      const { status, message, data } = response.data;

      if (status === 'success') {
        setResult(data.detailed_result);  // Access detailed_result from data
      } else {
        setError(message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while processing the request.');
    }

    setIsRunning(false);
  };

  // Render results dynamically
  const renderResult = (data) => {
    if (!data) return null;

    if (typeof data === 'string') {
      try {
        data = JSON.parse(data);
      } catch (e) {
        return <p className="text-red-400">Error: Invalid result format</p>;
      }
    }

    if (Array.isArray(data)) {
      if (taskType === 'Interest Rate Extraction') {
        return (
          <div className="mt-4">
            <h4 className="text-md font-medium text-teal-400">Interest Rates</h4>
            <div className="overflow-x-auto mt-2">
              <table className="min-w-full bg-gray-700 rounded-lg overflow-hidden">
                <thead className="bg-gray-800">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Category</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Rate Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Rate</th>
                    <th className="px-4 py-2 text-left text-xs font-medium from-gray-700 to-gray-600 text-gray-400 uppercase tracking-wider">Term</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Minimum Balance</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Currency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-600">
                  {data.map((item, index) => (
                    <tr key={index}>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.category || 'N/A'}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.rate_type || 'N/A'}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.rate || 'N/A'}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.term || 'N/A'}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.minimum_balance || 'N/A'}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.currency || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      } else if (taskType === 'Real Estate Listings') {
        return (
          <div className="mt-4 space-y-6">
            {data.map((listing, index) => (
              <div key={index} className="p-4 bg-gray-700 rounded-lg border border-gray-600">
                <h4 className="text-md font-medium text-teal-400">{listing.name || `Listing ${index + 1}`}</h4>
                <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">Address</p>
                    <p className="text-gray-300">{listing.address || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Price</p>
                    <p className="text-gray-300">{listing.price || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Beds</p>
                    <p className="text-gray-300">{listing.number_of_beds || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Size</p>
                    <p className="text-gray-300">{listing.size || 'N/A'}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-sm text-gray-400">Amenities</p>
                  <p className="text-gray-300">{listing.amenities || 'N/A'}</p>
                </div>
              </div>
            ))}
          </div>
        );
      }
    }

    return <p className="text-red-400">Error: Unexpected result format</p>;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="h-8 w-8 text-teal-400" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">
                Web Data Extractor Pro
              </h1>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                className="p-2 rounded-full hover:bg-gray-800 transition-colors"
                aria-label="Settings"
              >
                <Settings className="h-5 w-5 text-gray-400" />
              </button>
              <button 
                className="p-2 rounded-full hover:bg-gray-800 transition-colors"
                aria-label="Help"
                onClick={() => setActiveTab(activeTab === 'help' ? 'extraction' : 'help')}
              >
                <HelpCircle className="h-5 w-5 text-gray-400" />
              </button>
            </div>
          </div>
          <p className="text-gray-400 mt-2">Extract structured data from websites with AI precision</p>
        </header>

        {/* Tabs */}
        <div className="flex border-b border-gray-800 mb-6">
          <button
            className={`px-4 py-2 font-medium ${activeTab === 'extraction' ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-gray-300'}`}
            onClick={() => setActiveTab('extraction')}
          >
            Extraction Tool
          </button>
          <button
            className={`px-4 py-2 font-medium ${activeTab === 'help' ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-gray-300'}`}
            onClick={() => setActiveTab('help')}
          >
            Help & About
          </button>
        </div>

        {activeTab === 'extraction' ? (
          <div className="space-y-6">
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* URL Input */}
                <div className="md:col-span-2">
                  <label htmlFor="url" className="block text-sm font-medium text-gray-300 mb-2">
                    Website URL
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Globe className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      type="url"
                      id="url"
                      className="bg-gray-800 block w-full pl-10 pr-3 py-3 border border-gray-700 rounded-md focus:ring-teal-500 focus:border-teal-500 text-gray-100"
                      placeholder="https://example.com/path"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      required
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-400">Provide a valid URL with the information you want to extract</p>
                </div>

                {/* Task Type */}
                <div>
                  <label htmlFor="taskType" className="block text-sm font-medium text-gray-300 mb-2">
                    Task Type
                  </label>
                  <select
                    id="taskType"
                    className="bg-gray-800 block w-full py-3 px-3 border border-gray-700 rounded-md focus:ring-teal-500 focus:border-teal-500 text-gray-100"
                    value={taskType}
                    onChange={(e) => setTaskType(e.target.value)}
                  >
                    <option>Interest Rate Extraction</option>
                    <option>Real Estate Listings</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-400">Choose what type of data to retrieve</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Location Input - only visible for Real Estate task */}
                {taskType === 'Real Estate Listings' && (
                  <div>
                    <label htmlFor="location" className="block text-sm font-medium text-gray-300 mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      id="location"
                      className="bg-gray-800 block w-full px-3 py-3 border border-gray-700 rounded-md focus:ring-teal-500 focus:border-teal-500 text-gray-100"
                      placeholder="e.g., Mumbai, India"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                    />
                    <p className="mt-1 text-xs text-gray-400">Provide the location for real estate listings</p>
                  </div>
                )}

                {/* Additional Instructions */}
                <div className={taskType === 'Real Estate Listings' ? '' : 'md:col-span-2'}>
                  <label htmlFor="instructions" className="block text-sm font-medium text-gray-300 mb-2">
                    Additional Instructions (Optional)
                  </label>
                  <textarea
                    id="instructions"
                    rows="3"
                    className="bg-gray-800 block w-full px-3 py-3 border border-gray-700 rounded-md focus:ring-teal-500 focus:border-teal-500 text-gray-100"
                    placeholder="e.g., Click 'View Rates' button if needed, or navigate to relevant tabs"
                    value={additionalInstructions}
                    onChange={(e) => setAdditionalInstructions(e.target.value)}
                  />
                  <p className="mt-1 text-xs text-gray-400">Specify any custom extraction instructions to help the agent</p>
                </div>
              </div>

              {/* Tips Section */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-sm font-medium text-gray-300 flex items-center">
                    <Info className="h-4 w-4 mr-1 text-teal-400" />
                    Tips for better extraction
                  </h3>
                  <button 
                    type="button"
                    className="text-gray-400 hover:text-gray-300"
                    onClick={() => setShowTips(!showTips)}
                  >
                    {showTips ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                  </button>
                </div>
                
                {showTips && (
                  <div className="bg-gray-800 border-l-4 border-teal-400 rounded p-4 text-sm text-gray-300">
                    <ul className="list-disc ml-5 space-y-1">
                      <li>For interest rates, provide the exact page containing the rate tables</li>
                      <li>For real estate, additional instructions like "Filter for 2+ bedroom apartments" can help</li>
                      <li>If data isn't appearing, try adding instructions like "Click on 'View Details' button"</li>
                    </ul>
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="flex justify-center md:justify-start">
                <button
                  type="submit"
                  disabled={isRunning || !url}
                  className="px-6 py-3 bg-gradient-to-r from-teal-500 to-blue-500 text-white font-medium rounded-md hover:from-teal-600 hover:to-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 ease-out flex items-center"
                >
                  {isRunning ? (
                    <>
                      <RefreshCcw className="animate-spin -ml-1 mr-2 h-4 w-4" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <ArrowRight className="-ml-1 mr-2 h-4 w-4" />
                      Start Extraction
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Progress and Results Section */}
            {(isRunning || result || error) && (
              <div className="mt-8 space-y-6">
                {/* Progress Indicator */}
                {isRunning && (
                  <div className="bg-gray-800 rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-200 mb-4">Extraction Progress</h3>
                    <div className="w-full bg-gray-700 rounded-full h-2 mb-6">
                      <div 
                        className="bg-gradient-to-r from-teal-500 to-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
                        style={{ width: `${progress * 100}%` }}
                      ></div>
                    </div>
                    <div className="space-y-3">
                      {executionSteps.map((step, index) => (
                        <div key={index} className="flex items-start space-x-3 animate-fadeIn">
                          <div className="bg-gray-700 rounded-full p-1 mt-1">
                            <Check className="h-3 w-3 text-teal-400" />
                          </div>
                          <p className="text-gray-300">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {error && (
                  <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-red-500">
                    <h3 className="text-lg font-medium text-red-400 mb-4">Error</h3>
                    <p className="text-gray-300">{typeof error === 'string' ? error : error.msg || JSON.stringify(error)}</p>
                  </div>
                )}

                {/* Results */}
                {result && (
                  <div className="bg-gray-800 rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-200 mb-4">Extraction Results</h3>
                    {renderResult(result)}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-medium text-gray-200 mb-4">How to Use This Tool</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-teal-400 mb-2">For Interest Rate Extraction:</h3>
                <ol className="list-decimal ml-5 space-y-2 text-gray-300">
                  <li>Enter the URL of a banking website that shows interest rates</li>
                  <li>Select "Interest Rate Extraction" from the dropdown</li>
                  <li>Add any additional instructions (like "Click on Base Rate tab")</li>
                  <li>Click "Start Extraction"</li>
                </ol>
              </div>
              <div>
                <h3 className="text-lg font-medium text-teal-400 mb-2">For Real Estate Listings:</h3>
                <ol className="list-decimal ml-5 space-y-2 text-gray-300">
                  <li>Enter the URL of a real estate listing page</li>
                  <li>Select "Real Estate Listings" from the dropdown</li>
                  <li>Enter the location information (e.g., "Mumbai, India")</li>
                  <li>Add any filtering instructions if needed</li>
                  <li>Click "Start Extraction"</li>
                </ol>
              </div>
              <div>
                <h3 className="text-lg font-medium text-teal-400 mb-2">Troubleshooting:</h3>
                <div className="bg-gray-700 border-l-4 border-yellow-500 p-4 rounded">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    </div>
                    <div className="ml-3">
                      <ul className="list-disc ml-5 space-y-2 text-gray-300">
                        <li>If no data appears, try a more specific URL that directly shows the data</li>
                        <li>Add instructions like "Scroll down to view all results" or "Click on expand buttons"</li>
                        <li>Some websites may have anti-scraping measures that prevent extraction</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-gray-700">
                <p className="text-gray-400 text-sm">
                  This tool uses an AI-powered browser agent to navigate websites and extract structured data, 
                  similar to how a human would interact with the page. The extraction process is fully automated 
                  but may take a few moments to complete as it involves launching a browser and analyzing the webpage.
                </p>
              </div>
            </div>
          </div>
        )}
        <footer className="mt-12 pt-6 border-t border-gray-800 text-gray-400 text-sm">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p>© 2025 Web Data Extractor Pro</p>
            <div className="flex space-x-4 mt-4 md:mt-0">
              <a href="/privacy" className="hover:text-teal-400 transition-colors">Privacy Policy</a>
              <a href="/terms" className="hover:text-teal-400 transition-colors">Terms of Service</a>
              <a href="/contact" className="hover:text-teal-400 transition-colors">Contact</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}