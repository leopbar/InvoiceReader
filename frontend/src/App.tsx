/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm p-8 text-center space-y-4 border border-gray-100">
        <h1 className="text-2xl font-semibold text-gray-900">Invoice Reader</h1>
        <p className="text-gray-500">
          Frontend is running! The FastAPI backend is located in the <code>/backend</code> directory.
        </p>
        <div className="bg-blue-50 text-blue-700 text-sm rounded-lg p-4 text-left">
          <strong>Note:</strong> This preview environment runs Node.js. To run the Python backend, export the project and run it locally.
        </div>
      </div>
    </div>
  );
}
