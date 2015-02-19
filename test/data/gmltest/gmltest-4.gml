graph [
  is_directed 0
  node [
    id 1
    label "assemblage-1"
    xcoord 9
    ycoord 4
  ]
  node [
    id 3
    label "assemblage-3"
    xcoord 6
    ycoord 7
  ]
  node [
    id 4
    label "assemblage-4"
    xcoord 9
    ycoord 10
  ]
  edge [
    source 1
    target 3
    weight 1
    normalized_weight 0.1
  ]
  edge [
    source 1
    target 4
    weight 3
    normalized_weight 0.3
  ]
  edge [
    source 3
    target 4
    weight 3
    normalized_weight 0.3
  ]
]