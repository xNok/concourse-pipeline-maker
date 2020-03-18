Concourse pipeline maker - Generate Concourse pipeline from smaller chunks
===

## Objectif

> There is a real need to facilitate the reuse in concourse pipelines

> If you took are managing micro-services you know that there is no native way in Concourse to make batch modifications in pipelines and to historicize these changes.

> A pipeline of 1000 lines is a bit difficult to manage


The primary goal of this tool is to generate the pipeline manifest required by the ressource [concourse-pipeline-resource](https://github.com/concourse/concourse-pipeline-resource).

Additionally, it provide feature to improve the maintainability of your pipelines, such as:
  * Generating command line to manually set pipeline
  * Merge of pipeline (Therefore you can split yout yaml configuration in multiple files or override existing configuration)
  * Templating (reuse a configuration to generate similar pipeline)

## Usage

```
CONCOURSE PIPELINE MAKER

Usage:
  cpm find -i <inputfile> [-rv]
  cpm [options]
  cpm <pipeline_name>... [options]
  cpm -h | --help

Find Options:
  -r, --resources                           Extract all resource, when using cpm find
  -v, --vars                                Extract all variables, when using cpm find

Options:
  -i <inputfile>, --ifile <inputfile>       Path to the pipeline manifest. [default: pipeline-manifest.yml]
  -o <outputfile>, --ofile <outputfile>     Path to the output folder. [default: ./pipelines_files]
  -p <text_to_search:replacement_text>      Search and replace operation applied before procssing the pipeline manifest.
                                            Very usefull when working locally.
  -c <sfolder>, --ci <sfolder>              When publishing pipelines in a repo make sure it is compatible with concourse/concourse-pipeline-resource
  -x <cli_ext>, --cli <cli_ext>             Generate the Fly command line for each pipeline [default: cmd]
  Options-Flags:
  --copy                                    Systematically copy the pipeline in the output directory.
  --debug                                   Set the log level to debug
  -h, --help                                Show the help screen.
```

## Install

```bash
pip install git+[REPO_URL]
```

## The basis

`cpm` uses a manifest called `pipeline-manifest.yml` to store `fly set-pipeline` parameters for each pipeline to be set.

For instance:

```sh
fly set-pipeline -t my-team \
  -p service-dummy \
  -c ./pipelines/services-pipeline.yml \
  --load-vars-from ./vars/vars-dev.yml \
  --var "artifact_id=service-dummy"\
  --var "repo_id=service-dummy"
```

Is translated into a YAML Configuration as follow:

```yml
pipelines:
- -p: service-dummy
  -t: my-team
  -c: pipelines/services-pipeline.yml
  load-vars-from: vars/vars-dev.yml
  var:
    artifact_id: service-dummy
    repo_id: service-dummy
```


*The `pipelines` section* in `pipeline-manifest.yml` define the individual configuration for each pipeline

## Configuration section

*The `configs` section* in `pipeline-manifest.yml` may be use to define configuration that will be applied to every pipelines

For instance this is equal to the privious exemple:

```yml
configs:
  -t: my-team
  load-vars-from: vars/vars-dev.yml

pipelines:
- -p: service-dummy
  -c: pipelines/services-pipeline.yml
  var:
    artifact_id: service-dummy
    repo_id: service-dummy
```


### Valide pipeline configuration

* Arguments of `fly set_pipeline`:
  * `-t`, `team`: team / target
  * `pipeline`, `-p`: pipeline name (string)
  * `config`, `-c`: configurqation file for the pipeline (string)
  * `load-vars-from`, `-l`: variables file(s) (string or array)
  * `var`, `-v`: variables (JSON object)

* Arguments for configuration template:
    * `-tpl`, `template`: template to be use as a base for this pipeline

_See More things you can do with cpm_ to learn how to use templates

* Argument for merging pipelines:
    * `-m`, `merge`: yaml file(s) to be merge together in order (string or array)
    * `patials`: if provide folder name in `config`, `-c`, then you can list all the files you want to merge together from that folder

_See More things you can do with cpm_ to learn how to use merging pipelines

## More things you can do with cpm

### Templates = reuse pipeline configuration

*The `template`section* may be use to create reusable configuration. Later you can apply it by using the key `-tpl` ot `template` in your pipeline configuration

#### Example of configuration template

This configuration create a ppeline called `Test` using the confuguration from the template called `template`

```yml
configs:
  -t: team
  -l: ./pipelines_assets/vars-configs.yml
  -v:
    config: 1

templates:
  template-foo:
    -c: ./pipelines_assets/pipeline.yml
    -l: ./pipelines_assets/vars-template.yml
    -v:
      test: 1

pipelines:
- -p: Test
  -tpl: template-foo
  -v:
    test: 7
```

#### Use a seperate file for templates

Alternatively you can use a separate file for your templates. The previous example becomes:

`pipeline-manifest.yml`:

```yaml
configs:
  -t: team
  -l: ./pipelines_assets/vars-configs.yml
  -v:
    config: 1

templates_file: path/to/template_file.yml

pipelines:
- -p: Test
  -tpl: template-foo
  -v:
    test: 7
```

`templates_file.yml`:

```yaml
template-foo:
  -c: ./pipelines_assets/pipeline.yml
  -l: ./pipelines_assets/vars-template.yml
  -v:
    test: 1
```

### Merge = override or combine pipelines

This configuration will create a ppeline called `Test` by merging the files:
  * path/to/pipeline/buid_it.yml
  * path/to/pipeline/test_it.yml
  * path/to/pipeline/ship_it.yml

```yaml

configs:
  -t: team
  -l: ./pipelines_assets/vars-configs.yml

pipelines:
  - -p: Test
    -tpl: template
    -c: path/to/pipeline/buid_it.yml
    -m:
      path/to/pipeline/test_it.yml
      path/to/pipeline/ship_it.yml

```

### Partials = Building more Atomic pipleines

#### Example of configuration with Partials

This configuration will create a ppeline called `Test` by merging the files:
  * path/to/pipeline/folder/buid_it.yml
  * path/to/pipeline/folder/test_it.yml
  * path/to/pipeline/folder/ship_it.yml

```yml
configs:
  -t: team
pipelines:
  - -p: Test
    -c: path/to/pipeline/folder/
    partials:
    - buid_it
    - test_it
    - ship_it
```

#### Example of configuration with Partials and inplace replace

This configuration will create a ppeline called `Test` by merging the files:
  * path/to/pipeline/folder/buid_it.yml
  * path/to/pipeline/folder/test_it.yml
  * path/to/pipeline/folder/ship_it.yml and replace **((var))** by `foo`
  * path/to/pipeline/folder/ship_it.yml and replace **((var))** by `bar`

```yaml
configs:
  -t: team
pipelines:
  - -p: Test
    -c: path/to/pipeline/folder/
    partials:
    - buid_it
    - test_it
    - config_file: ship_it
      with: { "var": "bar" }
    - config_file: ship_it
      with: { "var": "foo" }
```

### Resources = manage resources in a separate file

Ressource are often the same accross multiple pipelines, therefore it would be nice to reduce duplication and define them in a single file. However, not every ressource should be added to every pipelines. The `resources_file` or `-r` flag let you declare a file to be merge in your pipeline, but unused *resources* and *resource_types* will be ignored.

#### Example of configuration with Resources files

This configuration will create a ppeline called `Test` by merging the files:
* path/to/pipeline/buid_it.yml
* path/to/resources/ressource.yml (but removes *resources* and *resource_types* not in path/to/pipeline/buid_it.yml)


```yml
configs:
  -t: team
  -r:
  - path/to/resource_file.yml
pipelines:
  - -p: Test
    -c: path/to/pipeline/folder/build_it.yml
```

## Helper `cpm find` (Beta)

This command line help you analyse an existing pipeline, for instance:

* Extract all variables, usefull to make sure you defined all the param in your variable file

## Use case of cpm

I wanna generate and set pipelines locally:
```bash
# Process the pipeline manifest
cpm
# Process only 1 pipeline and give me the fly command to execute
cpm my_pipilene
# Process all pipeline and generate the fly command line as .cmd files
cpm --cli cmd
# Process all pipeline and generate the fly command line as .sh files
cpm --cli sh
# Process all pipeline and copy all files in the output folder
cpm --copy
# My pipeline are in an other location and I use a generic name for it
cpm -p alias:path/to/the/folder
```

## Reusable commandline configuration (.cpmrc)

You may choose to define a runtime configuration in a file `.cpmrc`. Place that file at the location you arr usually run cpm from and paste into it your configuration.

Cpm configuration is printed at each execution in the terminal and look like this:

```json
{
  "--ci": None,
  "--cli": False,
  "--copy": False,
  "--debug": False,
  "--help": False,
  "--ifile": "pipelinemanifest.json",
  "--ofile": "./pipelines_files",
  "-p": [],
  "<pipeline_name>": []
}
```