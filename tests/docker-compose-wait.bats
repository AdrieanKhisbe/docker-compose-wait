@test "simple" {
  dc=tests/dockerfiles/docker-compose-simple.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc
  [ "$status" -eq 0 ]
  docker-compose -f $dc down
}

@test "fail" {
  dc=tests/dockerfiles/docker-compose-fail.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc
  [ "$status" -eq 255 ]
  docker-compose -f $dc down
}

@test "no healthcheck" {
  dc=tests/dockerfiles/docker-compose-no-healthcheck.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc
  [ "$status" -eq 0 ]
  docker-compose -f $dc down
}

@test "down" {
  dc=tests/dockerfiles/docker-compose-down.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc
  [ "$status" -eq 255 ]
  docker-compose -f $dc down
}

@test "2.1" {
  dc=tests/dockerfiles/docker-compose-2.1.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc
  [ "$status" -eq 0 ]
  docker-compose -f $dc down
}

@test "no wait" {
  dc=tests/dockerfiles/docker-compose-wait.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc
  [ "$status" -eq 255 ]
  [[ "$output" = *test1* ]]
  [[ ! "$output" = *test2* ]]
  docker-compose -f $dc down
}

@test "wait" {
  dc=tests/dockerfiles/docker-compose-wait.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc -w
  [ "$status" -eq 255 ]
  [[ "$output" = *test1* ]]
  [[ "$output" = *test2* ]]
  docker-compose -f $dc down
}

@test "timeout" {
  dc=tests/dockerfiles/docker-compose-timeout.yml
  docker-compose -f $dc up -d
  run python ./docker_compose_wait.py -f $dc -t 2s
  [ "$status" -eq 1 ]
  docker-compose -f $dc down
}
