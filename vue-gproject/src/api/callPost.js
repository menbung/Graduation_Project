import { postRecommend } from './client'

export async function callModel1(music) {
  const payload = {
    model_id: 1,
    seeds: music,
    k_neighbors: 3,
    per_seed_top: 3,
    final_top: 3,
    vector_cols: ['genre_vector', 'mood_vector', 'texture_vector'],
  }
  const data = await postRecommend(payload)
  if (!data || !Array.isArray(data.final_top_labels)) {
    console.error('final_top_labels가 응답에 없거나 배열이 아님:', data)
    return []
  }

  const styleLabels = data.final_top_labels.map((label) => {
    if (typeof label !== 'string') return ''
    return label.split('/')[0].trim()
  })

  return styleLabels
}
