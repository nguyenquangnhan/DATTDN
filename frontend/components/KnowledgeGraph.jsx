'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Share2, Loader, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react'
import { getNotebookGraph } from '../lib/api'

// Dynamic import for react-force-graph-2d (requires window)
let ForceGraph2D = null

// Color mapping for entity types
const TYPE_COLORS = {
  Person: '#818cf8',       // Indigo
  Organization: '#fbbf24', // Amber
  Location: '#34d399',     // Emerald
  Concept: '#60a5fa',      // Blue
  Event: '#f87171',        // Red
  Date: '#a78bfa',         // Violet
  Technology: '#22d3ee',   // Cyan
  Product: '#fb923c',      // Orange
  Document: '#94a3b8',     // Slate
}

function getNodeColor(type) {
  return TYPE_COLORS[type] || '#64748b'
}

export default function KnowledgeGraph({ notebookId }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [hoveredNode, setHoveredNode] = useState(null)
  const [graphReady, setGraphReady] = useState(false)
  const graphRef = useRef(null)
  const containerRef = useRef(null)

  // Dynamically import ForceGraph2D on client
  useEffect(() => {
    import('react-force-graph-2d').then((mod) => {
      ForceGraph2D = mod.default
      setGraphReady(true)
    })
  }, [])

  const loadGraph = useCallback(async () => {
    if (!notebookId) return

    setIsLoading(true)
    setError('')

    try {
      const data = await getNotebookGraph(notebookId)
      const nodes = (data.nodes || []).map((n) => ({
        id: n.id,
        name: n.name,
        type: n.type,
        description: n.description,
        val: 3,
      }))
      const links = (data.edges || []).map((e, idx) => ({
        source: e.source,
        target: e.target,
        type: e.type,
        description: e.description,
        id: `edge-${idx}`,
      }))

      setGraphData({ nodes, links })
    } catch (err) {
      console.error('Error loading graph:', err)
      setError(err.message || 'Failed to load knowledge graph')
    } finally {
      setIsLoading(false)
    }
  }, [notebookId])

  useEffect(() => {
    loadGraph()
  }, [loadGraph])

  const handleZoomIn = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom()
      graphRef.current.zoom(currentZoom * 1.5, 300)
    }
  }

  const handleZoomOut = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom()
      graphRef.current.zoom(currentZoom / 1.5, 300)
    }
  }

  // Get unique entity types for legend
  const entityTypes = [...new Set(graphData.nodes.map((n) => n.type))]

  if (!notebookId) return null

  return (
    <div className="surface-card rounded-xl overflow-hidden flex flex-col h-[500px] relative">
      {/* Header */}
      <div className="border-b border-slate-200/60 px-5 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-2">
          <Share2 className="h-5 w-5 text-violet-500" />
          <h2 className="text-base font-semibold text-slate-800">Knowledge Graph</h2>
          {graphData.nodes.length > 0 && (
            <span className="text-xs text-slate-500 ml-1">
              ({graphData.nodes.length} entities, {graphData.links.length} relations)
            </span>
          )}
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={handleZoomIn}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            onClick={loadGraph}
            disabled={isLoading}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Graph Area */}
      <div className="flex-1 relative" ref={containerRef}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="flex items-center space-x-2">
              <Loader className="h-5 w-5 animate-spin text-blue-500" />
              <span className="text-sm text-slate-600">Loading graph...</span>
            </div>
          </div>
        )}
 
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center p-4">
              <p className="text-sm text-red-500">{error}</p>
              <button
                onClick={loadGraph}
                className="mt-2 text-sm text-blue-500 hover:text-blue-600 transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        )}
 
        {!isLoading && !error && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-14 h-14 mx-auto mb-3 rounded-xl bg-slate-100 flex items-center justify-center">
                <Share2 className="h-7 w-7 text-slate-400" />
              </div>
              <p className="text-sm text-slate-500">No knowledge graph data yet</p>
              <p className="text-xs text-slate-400 mt-1">Upload documents to build the graph</p>
            </div>
          </div>
        )}

        {graphReady && ForceGraph2D && graphData.nodes.length > 0 && (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={containerRef.current?.clientWidth || 400}
            height={containerRef.current?.clientHeight || 350}
            backgroundColor="transparent"
            nodeLabel={(node) =>
              `${node.name} (${node.type})${node.description ? '\n' + node.description : ''}`
            }
            nodeColor={(node) => getNodeColor(node.type)}
            nodeRelSize={6}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.name
              const fontSize = Math.max(10 / globalScale, 2)
              const nodeR = 5

              // Node circle with glow
              ctx.beginPath()
              ctx.arc(node.x, node.y, nodeR + 2, 0, 2 * Math.PI)
              ctx.fillStyle = getNodeColor(node.type) + '20'
              ctx.fill()

              ctx.beginPath()
              ctx.arc(node.x, node.y, nodeR, 0, 2 * Math.PI)
              ctx.fillStyle = getNodeColor(node.type)
              ctx.fill()

              // Label
              if (globalScale > 0.6) {
                ctx.font = `${fontSize}px Inter, system-ui, sans-serif`
                ctx.textAlign = 'center'
                ctx.textBaseline = 'top'
                ctx.fillStyle = '#334155'
                ctx.fillText(label, node.x, node.y + nodeR + 3)
              }
            }}
            linkLabel={(link) => link.type}
            linkColor={() => 'rgba(148, 163, 184, 0.15)'}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkDirectionalArrowColor={() => 'rgba(148, 163, 184, 0.3)'}
            linkCurvature={0.1}
            onNodeHover={(node) => setHoveredNode(node)}
            onNodeClick={(node) => {
              if (graphRef.current) {
                graphRef.current.centerAt(node.x, node.y, 500)
                graphRef.current.zoom(3, 500)
              }
            }}
            cooldownTicks={100}
            onEngineStop={() => {
              if (graphRef.current) {
                graphRef.current.zoomToFit(400, 40)
              }
            }}
          />
        )}
      </div>

      {/* Legend */}
      {entityTypes.length > 0 && (
        <div className="border-t border-slate-200/60 px-5 py-2 flex-shrink-0">
          <div className="flex flex-wrap gap-3">
            {entityTypes.map((type) => (
              <div key={type} className="flex items-center space-x-1.5">
                <div
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: getNodeColor(type) }}
                />
                <span className="text-xs text-slate-500">{type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
 
      {/* Hovered Node Info */}
      {hoveredNode && (
        <div className="absolute bottom-12 left-4 glass-card rounded-xl p-3 max-w-xs z-20 animate-fade-in">
          <p className="text-sm font-semibold text-slate-800">{hoveredNode.name}</p>
          <p className="text-xs text-slate-500">{hoveredNode.type}</p>
          {hoveredNode.description && (
            <p className="text-xs text-slate-600 mt-1">{hoveredNode.description}</p>
          )}
        </div>
      )}
    </div>
  )
}
