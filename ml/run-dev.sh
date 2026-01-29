#!/bin/bash

sudo nerdctl --address /run/k3s/containerd/containerd.sock run -d \
    --name faqman-ml \
    --network faqman \
    --pull never \
    -v $(pwd):/app \
    faqman-ml:latest \
    sleep infinity
