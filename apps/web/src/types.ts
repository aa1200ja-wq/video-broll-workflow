export type Scene = {
  id: string
  order: number
  narration: string
  start: number
  end: number
  search_query: string
  selected_asset: string | null
  selected_asset_type: 'video' | 'image' | null
  source_name: string | null
  source_url: string | null
  status: string
}

export type Project = {
  id: string
  name: string
  script: string
  voice: string
  rate: string
  pitch: string
  width: number
  height: number
  scenes: Scene[]
}

export type SearchResult = {
  id: string
  source: string
  media_type: 'video' | 'image'
  preview_url: string
  download_url: string
  page_url: string
  author: string
  width: number
  height: number
  duration: number
}
